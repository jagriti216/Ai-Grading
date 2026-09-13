"""
Data preparation for DeBERTa answer grading model.

Datasets:
  1. SciEntsBank — science, categorical labels 0-3
  2. Mohler open-ended — CS/programming, continuous scores 0-5

Output columns (standardized):
  question, expected_answer, student_answer, normalized_score

normalized_score is always 0.0 to 1.0
Multiply by max_marks at inference time to get final score.
"""

import os
import json
import pandas as pd
from sklearn.model_selection import train_test_split

# ── paths (relative to this file) ───────────────────────────────────────
BASE         = os.path.dirname(__file__)
SCIENTSBANK_DIR = os.path.join(BASE, "..", "..", "datasets", "scientsbank")
MOHLER_PATH     = os.path.join(BASE, "..", "..", "datasets", "mohler", "mohler_open_ended.csv")
OUTPUT_DIR      = os.path.join(BASE, "..", "data")

SCIENTSBANK_FILES = ["train.csv", "test_ua.csv", "test_ud.csv", "test_uq.csv"]

# SciEntsBank label → normalized score
LABEL_TO_SCORE = {
    0: 1.0,   # correct
    2: 0.5,   # partially correct
    1: 0.0,   # contradictory
    3: 0.0,   # non-domain
    # label 4 dropped
}


def load_scientsbank() -> pd.DataFrame:
    dfs = []
    for fname in SCIENTSBANK_FILES:
        path = os.path.join(SCIENTSBANK_DIR, fname)
        if not os.path.exists(path):
            print(f"  Warning: {fname} not found, skipping")
            continue
        df = pd.read_csv(path)
        print(f"  Loaded {fname}: {len(df)} rows")
        dfs.append(df)

    if not dfs:
        raise FileNotFoundError(f"No SciEntsBank CSVs found in {SCIENTSBANK_DIR}")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined[combined["label"] != 4]
    combined = combined.dropna(subset=["question", "reference_answer", "student_answer", "label"])
    combined = combined.drop_duplicates(subset=["question", "student_answer"])
    combined["normalized_score"] = combined["label"].map(LABEL_TO_SCORE)
    combined = combined.rename(columns={"reference_answer": "expected_answer"})
    combined["source"] = "scientsbank"

    return combined[["question", "expected_answer", "student_answer", "normalized_score", "source"]]


def load_mohler() -> pd.DataFrame:
    if not os.path.exists(MOHLER_PATH):
        raise FileNotFoundError(f"Mohler CSV not found at {MOHLER_PATH}")

    df = pd.read_csv(MOHLER_PATH)
    print(f"  Loaded mohler_open_ended: {len(df)} rows")

    df = df.dropna(subset=["question", "instructor_answer", "student_answer", "score_avg"])
    df = df.drop_duplicates(subset=["question", "student_answer"])
    df["normalized_score"] = (df["score_avg"] / 5.0).round(4)
    df = df.rename(columns={"instructor_answer": "expected_answer"})
    df["source"] = "mohler"

    return df[["question", "expected_answer", "student_answer", "normalized_score", "source"]]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading SciEntsBank...")
    df_sci = load_scientsbank()
    print(f"  Clean: {len(df_sci)} rows")

    print("\nLoading Mohler...")
    df_mol = load_mohler()
    print(f"  Clean: {len(df_mol)} rows")

    combined = pd.concat([df_sci, df_mol], ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"\nCombined: {len(combined)} rows")

    train, temp = train_test_split(combined, test_size=0.20, random_state=42)
    val, test   = train_test_split(temp,     test_size=0.50, random_state=42)

    print(f"  Train : {len(train)} rows")
    print(f"  Val   : {len(val)} rows")
    print(f"  Test  : {len(test)} rows")

    train.to_csv(os.path.join(OUTPUT_DIR, "train.csv"), index=False)
    val.to_csv(  os.path.join(OUTPUT_DIR, "val.csv"),   index=False)
    test.to_csv( os.path.join(OUTPUT_DIR, "test.csv"),  index=False)

    stats = {
        "total_rows": len(combined),
        "train_rows": len(train),
        "val_rows":   len(val),
        "test_rows":  len(test),
        "sources": {
            "scientsbank": len(df_sci),
            "mohler":      len(df_mol)
        },
        "score_stats": {
            "mean": round(combined["normalized_score"].mean(), 4),
            "std":  round(combined["normalized_score"].std(),  4),
            "min":  round(combined["normalized_score"].min(),  4),
            "max":  round(combined["normalized_score"].max(),  4),
        },
        "avg_lengths": {
            "question":        int(combined["question"].str.len().mean()),
            "expected_answer": int(combined["expected_answer"].str.len().mean()),
            "student_answer":  int(combined["student_answer"].str.len().mean()),
        }
    }

    with open(os.path.join(OUTPUT_DIR, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\nStats:")
    print(f"  SciEntsBank : {stats['sources']['scientsbank']} rows")
    print(f"  Mohler      : {stats['sources']['mohler']} rows")
    print(f"  Score mean  : {stats['score_stats']['mean']}")
    print(f"  Score std   : {stats['score_stats']['std']}")
    print(f"\nSaved to {OUTPUT_DIR}/")
    print("  train.csv, val.csv, test.csv, stats.json")
    print("\nData prep complete. Ready for training.")


if __name__ == "__main__":
    main()
