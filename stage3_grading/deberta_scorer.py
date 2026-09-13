"""
Loads trained DeBERTa model from HuggingFace and scores answers 0-1.
Model: jags020106/deberta-answer-grader
"""

import os
import torch
from torch import nn
from transformers import AutoTokenizer, AutoModel
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv
# Try loading from the root .env first
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(root_env):
    load_dotenv(root_env)
else:
    # Fallback to stage1_extraction/.env
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "stage1_extraction", ".env"))
    # Generic load_dotenv searching current & parent directories
    load_dotenv()

HF_TOKEN  = os.getenv("HF_API_KEY")
REPO      = "jags020106/deberta-answer-grader"
MAX_LEN   = 256
DEVICE    = "cuda" if torch.cuda.is_available() else "cpu"

# singleton — load once, reuse
_tokenizer = None
_model     = None


class AnswerGrader(nn.Module):
    def __init__(self, dropout=0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(
            REPO,
            token                   = HF_TOKEN,
            ignore_mismatched_sizes = True
        )
        hidden_size    = self.encoder.config.hidden_size
        self.regressor = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, 1),
            nn.Sigmoid()
        ).float()

    def forward(self, input_ids, attention_mask):
        outputs    = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :].float()
        return self.regressor(cls_output).squeeze(-1)


def load_model():
    global _tokenizer, _model
    if _model is None:
        print("Loading DeBERTa model from HuggingFace...")
        _tokenizer = AutoTokenizer.from_pretrained(REPO, token=HF_TOKEN)
        _model     = AnswerGrader()
        weights    = hf_hub_download(repo_id=REPO, filename="pytorch_model.bin", token=HF_TOKEN)
        _model.load_state_dict(torch.load(weights, map_location=DEVICE))
        _model.to(DEVICE)
        _model.eval()
        print("DeBERTa loaded successfully")
    return _tokenizer, _model


def get_deberta_score(question: str, expected_answer: str, student_answer: str) -> float:
    """
    Returns a score between 0 and 1.
    0 = completely wrong, 1 = perfectly correct.
    """
    if not student_answer or not student_answer.strip():
        return 0.0

    tokenizer, model = load_model()

    text = (
        f"question: {question} "
        f"[SEP] expected: {expected_answer} "
        f"[SEP] student: {student_answer}"
    )

    enc = tokenizer(
        text,
        return_tensors = "pt",
        max_length     = MAX_LEN,
        padding        = "max_length",
        truncation     = True
    )

    with torch.no_grad():
        score = model(
            enc["input_ids"].to(DEVICE),
            enc["attention_mask"].to(DEVICE)
        )

    return round(float(score.item()), 4)


if __name__ == "__main__":
    tests = [
        {
            "question":        "What is photosynthesis?",
            "expected_answer": "Photosynthesis is the process by which plants convert CO2 and water into glucose using sunlight.",
            "student_answer":  "Plants use sunlight and carbon dioxide to make food."
        },
        {
            "question":        "What is photosynthesis?",
            "expected_answer": "Photosynthesis is the process by which plants convert CO2 and water into glucose using sunlight.",
            "student_answer":  "Plants drink water at night to grow."
        },
    ]

    for t in tests:
        score = get_deberta_score(t["question"], t["expected_answer"], t["student_answer"])
        print(f"Score: {score:.4f} | Student: {t['student_answer'][:50]}")
