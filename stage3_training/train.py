"""
DeBERTa-v3-base Fine-tuning for Answer Grading
Fixed: nan loss, fp32 forced, lower LR, gradient accumulation
"""

import os
import json
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from torch.optim import AdamW
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error

CONFIG = {
    "model_name":     "microsoft/deberta-v3-base",
    "hf_repo":        "jags020106/deberta-answer-grader",
    "max_length":     256,
    "batch_size":     4,
    "grad_accum":     4,       # effective batch = 4x4 = 16
    "epochs":         5,
    "encoder_lr":     5e-6,   # very low for encoder stability
    "head_lr":        5e-5,   # higher for new head
    "warmup_ratio":   0.1,
    "dropout":        0.1,
    "seed":           42,
    "device":         "cuda" if torch.cuda.is_available() else "cpu"
}

TRAIN_PATH = "/content/data/train.csv"
VAL_PATH   = "/content/data/val.csv"
TEST_PATH  = "/content/data/test.csv"
OUTPUT_DIR = "/content/model_output"
HF_TOKEN   = "hf_your_read_token_here"

print(f"Device : {CONFIG['device']}")
print(f"Config : encoder_lr={CONFIG['encoder_lr']} head_lr={CONFIG['head_lr']} "
      f"batch={CONFIG['batch_size']} grad_accum={CONFIG['grad_accum']}")

torch.manual_seed(CONFIG["seed"])
np.random.seed(CONFIG["seed"])


class AnswerGradingDataset(Dataset):
    def __init__(self, df, tokenizer, max_length):
        self.df         = df.reset_index(drop=True)
        self.tokenizer  = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row  = self.df.iloc[idx]
        text = (
            f"question: {str(row['question'])} "
            f"[SEP] expected: {str(row['expected_answer'])} "
            f"[SEP] student: {str(row['student_answer'])}"
        )
        encoding = self.tokenizer(
            text,
            max_length     = self.max_length,
            padding        = "max_length",
            truncation     = True,
            return_tensors = "pt"
        )
        return {
            "input_ids":      encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "score":          torch.tensor(float(row["normalized_score"]), dtype=torch.float32)
        }


class AnswerGrader(nn.Module):
    def __init__(self, model_name, dropout):
        super().__init__()

        # force float32 — avoids nan from fp16 mixed precision
        self.encoder = AutoModel.from_pretrained(
            model_name,
            ignore_mismatched_sizes = True,
            token                   = HF_TOKEN,
            torch_dtype             = torch.float32
        )

        hidden_size    = self.encoder.config.hidden_size
        self.regressor = nn.Sequential(
            nn.LayerNorm(hidden_size),   # normalize CLS before regression
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, 1),
            nn.Sigmoid()
        ).float()

        # xavier init
        for module in self.regressor.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, input_ids, attention_mask):
        outputs    = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :].float()
        score      = self.regressor(cls_output).squeeze(-1)
        return score


def compute_metrics(preds, labels):
    # guard against nan
    mask   = ~(np.isnan(preds) | np.isnan(labels))
    preds  = preds[mask]
    labels = labels[mask]

    if len(preds) == 0:
        return {"mse": 999, "rmse": 999, "pearson": 0.0, "qwk": 0.0}

    mse  = mean_squared_error(labels, preds)
    rmse = np.sqrt(mse)

    if np.std(preds) < 1e-6:
        pearson = 0.0
    else:
        pearson = pearsonr(preds, labels)[0]

    preds_scaled  = np.round(preds  * 4).astype(int).clip(0, 4)
    labels_scaled = np.round(labels * 4).astype(int).clip(0, 4)
    n           = len(preds_scaled)
    num_classes = 5
    W = np.zeros((num_classes, num_classes))
    for i in range(num_classes):
        for j in range(num_classes):
            W[i][j] = (i - j) ** 2 / (num_classes - 1) ** 2
    O = np.zeros((num_classes, num_classes))
    for p, l in zip(preds_scaled, labels_scaled):
        O[l][p] += 1
    E     = np.outer(O.sum(axis=1), O.sum(axis=0)) / n
    denom = (W * E).sum()
    qwk   = 1 - (W * O).sum() / denom if denom > 0 else 0.0

    return {
        "mse":     round(float(mse),     4),
        "rmse":    round(float(rmse),    4),
        "pearson": round(float(pearson), 4),
        "qwk":     round(float(qwk),     4)
    }


def train_epoch(model, loader, optimizer, scheduler, device, grad_accum):
    model.train()
    total_loss = 0
    criterion  = nn.MSELoss()
    optimizer.zero_grad()

    for i, batch in enumerate(loader):
        input_ids      = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        scores         = batch["score"].to(device).float()

        preds = model(input_ids, attention_mask)

        # check for nan before backward
        if torch.isnan(preds).any():
            print(f"  NaN detected at step {i+1}, skipping batch")
            optimizer.zero_grad()
            continue

        loss = criterion(preds, scores) / grad_accum
        loss.backward()

        if (i + 1) % grad_accum == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

        total_loss += loss.item() * grad_accum

        if (i + 1) % 200 == 0:
            print(f"    Step {i+1}/{len(loader)} loss={loss.item()*grad_accum:.4f} "
                  f"pred_mean={preds.mean().item():.3f} pred_std={preds.std().item():.3f}")

    return total_loss / len(loader)


def evaluate(model, loader, device):
    model.eval()
    all_preds  = []
    all_labels = []
    total_loss = 0
    criterion  = nn.MSELoss()

    with torch.no_grad():
        for batch in loader:
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            scores         = batch["score"].to(device).float()
            preds          = model(input_ids, attention_mask)

            if torch.isnan(preds).any():
                continue

            loss        = criterion(preds, scores)
            total_loss += loss.item()
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(scores.cpu().numpy())

    all_preds  = np.array(all_preds)
    all_labels = np.array(all_labels)

    print(f"    Pred  → mean={all_preds.mean():.3f} std={all_preds.std():.3f} "
          f"min={all_preds.min():.3f} max={all_preds.max():.3f}")
    print(f"    Label → mean={all_labels.mean():.3f} std={all_labels.std():.3f}")

    metrics         = compute_metrics(all_preds, all_labels)
    metrics["loss"] = round(total_loss / max(len(loader), 1), 4)
    return metrics


def main():
    device    = CONFIG["device"]
    grad_accum = CONFIG["grad_accum"]

    train_df = pd.read_csv(TRAIN_PATH)
    val_df   = pd.read_csv(VAL_PATH)
    test_df  = pd.read_csv(TEST_PATH)

    # drop any rows with nan scores
    train_df = train_df.dropna(subset=["normalized_score", "question", "expected_answer", "student_answer"])
    val_df   = val_df.dropna(subset=["normalized_score", "question", "expected_answer", "student_answer"])
    test_df  = test_df.dropna(subset=["normalized_score", "question", "expected_answer", "student_answer"])

    print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")
    print(f"Score → mean={train_df['normalized_score'].mean():.3f} "
          f"std={train_df['normalized_score'].std():.3f}")

    print("\nLoading tokenizer...")
    tokenizer    = AutoTokenizer.from_pretrained(CONFIG["model_name"], token=HF_TOKEN)
    train_ds     = AnswerGradingDataset(train_df, tokenizer, CONFIG["max_length"])
    val_ds       = AnswerGradingDataset(val_df,   tokenizer, CONFIG["max_length"])
    test_ds      = AnswerGradingDataset(test_df,  tokenizer, CONFIG["max_length"])
    train_loader = DataLoader(train_ds, batch_size=CONFIG["batch_size"], shuffle=True,  num_workers=2, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=CONFIG["batch_size"], shuffle=False, num_workers=2, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=CONFIG["batch_size"], shuffle=False, num_workers=2, pin_memory=True)

    print("Loading model...")
    model = AnswerGrader(CONFIG["model_name"], CONFIG["dropout"]).to(device)

    # differential LR
    optimizer = AdamW([
        {"params": model.encoder.parameters(),   "lr": CONFIG["encoder_lr"],  "weight_decay": 0.01},
        {"params": model.regressor.parameters(), "lr": CONFIG["head_lr"],     "weight_decay": 0.0}
    ])

    total_steps  = (len(train_loader) // grad_accum) * CONFIG["epochs"]
    warmup_steps = int(total_steps * CONFIG["warmup_ratio"])
    scheduler    = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    # gradient check
    print("\nVerifying gradient flow...")
    model.train()
    batch = next(iter(train_loader))
    preds = model(batch["input_ids"].to(device), batch["attention_mask"].to(device))
    loss  = nn.MSELoss()(preds, batch["score"].to(device).float())
    loss.backward()
    enc_grad  = sum(p.grad.abs().mean().item() for p in model.encoder.parameters()  if p.grad is not None)
    head_grad = sum(p.grad.abs().mean().item() for p in model.regressor.parameters() if p.grad is not None)
    print(f"  Encoder gradient  : {enc_grad:.6f}")
    print(f"  Regressor gradient: {head_grad:.6f}")
    print(f"  First pred: {preds[0].item():.4f} (should not be nan)")
    optimizer.zero_grad()

    best_pearson    = -1
    best_model_path = "/content/best_model.pt"
    history         = []

    print(f"\n{'Epoch':<8}{'Train Loss':<14}{'Val Loss':<12}{'Pearson':<12}{'QWK':<10}")
    print("-" * 56)

    for epoch in range(1, CONFIG["epochs"] + 1):
        print(f"\nEpoch {epoch}/{CONFIG['epochs']}")
        train_loss  = train_epoch(model, train_loader, optimizer, scheduler, device, grad_accum)
        print("  Validation:")
        val_metrics = evaluate(model, val_loader, device)
        history.append({"epoch": epoch, "train_loss": round(train_loss, 4), **val_metrics})
        print(f"{epoch:<8}{train_loss:<14.4f}{val_metrics['loss']:<12.4f}"
              f"{val_metrics['pearson']:<12.4f}{val_metrics['qwk']:<10.4f}")

        if val_metrics["pearson"] > best_pearson:
            best_pearson = val_metrics["pearson"]
            torch.save(model.state_dict(), best_model_path)
            print(f"  → Best model saved (pearson={best_pearson:.4f})")

    print("\nTest evaluation...")
    model.load_state_dict(torch.load(best_model_path))
    test_metrics = evaluate(model, test_loader, device)
    print(f"\nTest Results:")
    print(f"  MSE     : {test_metrics['mse']}")
    print(f"  RMSE    : {test_metrics['rmse']}")
    print(f"  Pearson : {test_metrics['pearson']}")
    print(f"  QWK     : {test_metrics['qwk']}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tokenizer.save_pretrained(OUTPUT_DIR)
    model.encoder.config.save_pretrained(OUTPUT_DIR)
    torch.save(model.state_dict(), os.path.join(OUTPUT_DIR, "pytorch_model.bin"))

    with open(os.path.join(OUTPUT_DIR, "training_results.json"), "w") as f:
        json.dump({"config": CONFIG, "history": history,
                   "test_metrics": test_metrics, "best_pearson": best_pearson}, f, indent=2)

    print(f"\nSaved to {OUTPUT_DIR}")
    print("Training complete.")


def push_to_hub(hf_write_token: str):
    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(repo_id=CONFIG["hf_repo"], token=hf_write_token, exist_ok=True)
    api.upload_folder(folder_path=OUTPUT_DIR, repo_id=CONFIG["hf_repo"], token=hf_write_token)
    print(f"Pushed to: https://huggingface.co/{CONFIG['hf_repo']}")


if __name__ == "__main__":
    main()
    # push_to_hub("hf_your_write_token_here")
