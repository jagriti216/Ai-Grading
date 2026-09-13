"""
Standalone evaluation of the trained DeBERTa answer-grading model
(jags020106/deberta-answer-grader) against the held-out test set.

Reports both the regression metrics used during training (MSE, RMSE,
Pearson) and QWK, plus a discretized 5-class confusion matrix +
accuracy — useful for reporting/citing concrete numbers, since these
weren't saved anywhere after the original Colab training run.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error, confusion_matrix, accuracy_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from stage3_grading.deberta_scorer import load_model, DEVICE, MAX_LEN

TEST_PATH = os.path.join(os.path.dirname(__file__), "data", "test.csv")
OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "test_eval_results.json")


def compute_qwk(preds_scaled, labels_scaled, num_classes=5):
    n = len(preds_scaled)
    W = np.zeros((num_classes, num_classes))
    for i in range(num_classes):
        for j in range(num_classes):
            W[i][j] = (i - j) ** 2 / (num_classes - 1) ** 2
    O = np.zeros((num_classes, num_classes), dtype=int)
    for p, l in zip(preds_scaled, labels_scaled):
        O[l][p] += 1
    E = np.outer(O.sum(axis=1), O.sum(axis=0)) / n
    denom = (W * E).sum()
    qwk = 1 - (W * O).sum() / denom if denom > 0 else 0.0
    return qwk, O


def main():
    df = pd.read_csv(TEST_PATH)
    df = df.dropna(subset=["question", "expected_answer", "student_answer", "normalized_score"])
    print(f"Test rows: {len(df)}")

    tokenizer, model = load_model()

    preds = []
    with torch.no_grad():
        for i, row in df.iterrows():
            text = (
                f"question: {str(row['question'])} "
                f"[SEP] expected: {str(row['expected_answer'])} "
                f"[SEP] student: {str(row['student_answer'])}"
            )
            enc = tokenizer(
                text, return_tensors="pt", max_length=MAX_LEN,
                padding="max_length", truncation=True,
            )
            score = model(enc["input_ids"].to(DEVICE), enc["attention_mask"].to(DEVICE))
            preds.append(float(score.item()))

            if (len(preds)) % 100 == 0:
                print(f"  {len(preds)}/{len(df)}")

    preds = np.array(preds)
    labels = df["normalized_score"].to_numpy()

    mse = mean_squared_error(labels, preds)
    rmse = np.sqrt(mse)
    pearson = pearsonr(preds, labels)[0]

    preds_scaled = np.round(preds * 4).astype(int).clip(0, 4)
    labels_scaled = np.round(labels * 4).astype(int).clip(0, 4)

    qwk, O = compute_qwk(preds_scaled, labels_scaled)
    acc = accuracy_score(labels_scaled, preds_scaled)
    cm = confusion_matrix(labels_scaled, preds_scaled, labels=[0, 1, 2, 3, 4])

    # within-1-class accuracy (off by at most 1 grading band)
    within_1 = np.mean(np.abs(preds_scaled - labels_scaled) <= 1)

    results = {
        "test_rows": len(df),
        "mse": round(float(mse), 4),
        "rmse": round(float(rmse), 4),
        "pearson": round(float(pearson), 4),
        "qwk": round(float(qwk), 4),
        "accuracy_5class": round(float(acc), 4),
        "within_1_class_accuracy": round(float(within_1), 4),
        "confusion_matrix_5class": cm.tolist(),
        "class_labels": ["0 (0-0.1)", "1 (0.1-0.3)", "2 (0.3-0.5)", "3 (0.5-0.7)", "4 (0.7-1.0)"],
    }

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== Test Set Evaluation ===")
    print(f"MSE                    : {results['mse']}")
    print(f"RMSE                   : {results['rmse']}")
    print(f"Pearson correlation    : {results['pearson']}")
    print(f"QWK                    : {results['qwk']}")
    print(f"5-class accuracy       : {results['accuracy_5class']}")
    print(f"Within-1-class accuracy: {results['within_1_class_accuracy']}")
    print("\nConfusion matrix (rows=true, cols=predicted):")
    print(cm)
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
