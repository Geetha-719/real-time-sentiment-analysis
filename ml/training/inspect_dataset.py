"""Phase 1/2 - Dataset inspection.

Reads the raw Twitter sentiment CSVs, reports schema, class distribution,
missing values, duplicates and label mapping, then writes a JSON summary to
reports/dataset_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

COLS = ["id", "entity", "sentiment", "text"]


def load(path: Path) -> pd.DataFrame:
    # The raw Kaggle files have no header row.
    df = pd.read_csv(path, header=None, names=COLS, dtype=str)
    return df


def summarize(df: pd.DataFrame) -> dict:
    text = df["text"].fillna("").astype(str)
    lengths = text.str.len()
    dup_text = int(df.duplicated(subset=["text"]).sum())
    return {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "sentiment_counts": {k: int(v) for k, v in df["sentiment"].value_counts(dropna=False).items()},
        "entities": int(df["entity"].nunique()),
        "null_text": int(df["text"].isna().sum()),
        "empty_text": int((text.str.strip() == "").sum()),
        "null_sentiment": int(df["sentiment"].isna().sum()),
        "duplicate_text_rows": dup_text,
        "text_length_mean": round(float(lengths.mean()), 2),
        "text_length_median": float(lengths.median()),
        "text_length_max": int(lengths.max()),
    }


def main() -> int:
    summary: dict = {}
    frames = {}
    for name, fname in [("train", "twitter_training.csv"), ("validation", "twitter_validation.csv")]:
        path = RAW / fname
        if not path.exists():
            print(f"[skip] {path} not found")
            continue
        df = load(path)
        frames[name] = df
        summary[name] = summarize(df)
        print(f"\n=== {name}: {path.name} ===")
        for k, v in summary[name].items():
            print(f"  {k}: {v}")

    if "train" in frames and "validation" in frames:
        train_texts = set(frames["train"]["text"].dropna())
        overlap = int(frames["validation"]["text"].dropna().isin(train_texts).sum())
        summary["train_validation_text_overlap"] = overlap
        print(f"\ntrain/validation text overlap: {overlap}")

    # Conflicting labels for identical text (label noise signal)
    if "train" in frames:
        conflicts = int(frames["train"].groupby("text")["sentiment"].nunique().gt(1).sum())
        summary["conflicting_label_texts"] = conflicts
        summary["sentiment_label_mapping"] = {
            "Positive": "Positive sentiment",
            "Negative": "Negative sentiment",
            "Neutral": "Neutral sentiment",
            "Irrelevant": "Irrelevant / off-topic (kept as its own class unless dropped)",
        }
        print(f"texts with conflicting labels: {conflicts}")

    out = REPORTS / "dataset_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
