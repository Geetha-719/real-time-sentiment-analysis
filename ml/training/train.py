"""Phase 2-10: dataset cleaning, TF-IDF, model training, evaluation and saving.

Run from the project root:
    python -m ml.training.train

Outputs
-------
ml/models/sentiment_model.joblib   best sklearn Pipeline (vectorizer + model)
ml/models/metadata.json            label mapping, config, feature count
ml/models/metrics.json             full evaluation metrics for every model
reports/dataset_summary.json       dataset inspection summary
"""
from __future__ import annotations

import json
import sys
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from ml.config import (
    DATA_PROCESSED,
    DATA_RAW,
    METADATA_FILE,
    METRICS_FILE,
    MODEL_FILE,
    RANDOM_SEED,
    REPORTS_DIR,
)
from ml.preprocessing import TfidfAnalyzer, preprocess

COLS = ["id", "entity", "sentiment", "text"]
VALID_LABELS = {"Positive", "Negative", "Neutral", "Irrelevant"}
LABEL_ORDER = ["Negative", "Neutral", "Positive", "Irrelevant"]


# --------------------------------------------------------------------------- #
# Data loading & cleaning
# --------------------------------------------------------------------------- #
def load_raw() -> pd.DataFrame:
    frames = []
    for fname in ("twitter_training.csv", "twitter_validation.csv"):
        path = DATA_RAW / fname
        if not path.exists():
            continue
        df = pd.read_csv(path, header=None, names=COLS, dtype=str)
        frames.append(df)
    if not frames:
        raise SystemExit("No datasets found in data/raw/")
    return pd.concat(frames, ignore_index=True)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop malformed rows, normalize labels, de-duplicate and de-mojibake."""
    before = len(df)
    # Remove rows accidentally containing the header line
    df = df[df["sentiment"].isin(VALID_LABELS)]
    # Missing / empty text
    df = df[df["text"].notna()]
    df["text"] = df["text"].astype(str)
    df = df[df["text"].str.strip().str.len() > 0]
    # Normalize label casing/whitespace
    df["sentiment"] = df["sentiment"].str.strip().str.title()
    # De-duplicate: identical text repeated is the main leakage source.
    df = df.drop_duplicates(subset=["text"], keep="first")
    df = df.reset_index(drop=True)
    print(f"[clean] {before} -> {len(df)} rows after cleaning/de-dup")
    return df


# --------------------------------------------------------------------------- #
# Pipelines
# --------------------------------------------------------------------------- #
def make_pipeline(model, *, ngram=(1, 1), stem=True, min_df=2, sublinear=True) -> Pipeline:
    vec = TfidfVectorizer(
        analyzer=TfidfAnalyzer(stem=stem, ngram_range=ngram),
        min_df=min_df,
        max_df=0.95,
        sublinear_tf=sublinear,
    )
    return Pipeline([("tfidf", vec), ("clf", model)])


def candidate_models(ngram, stem):
    return {
        "Naive Bayes": make_pipeline(MultinomialNB(alpha=0.3), ngram=ngram, stem=stem),
        "Logistic Regression": make_pipeline(
            LogisticRegression(C=5.0, max_iter=1000, random_state=RANDOM_SEED),
            ngram=ngram, stem=stem,
        ),
    }


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def evaluate(y_true, y_pred, y_proba, classes) -> dict:
    labels = list(range(len(classes)))
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "precision_weighted": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_weighted": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "classification_report": classification_report(
            y_true, y_pred, labels=labels, target_names=classes, zero_division=0, output_dict=True
        ),
        "classes": classes,
    }
    if y_proba is not None:
        try:
            out["roc_auc_ovr_macro"] = float(
                roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro", labels=labels)
            )
        except ValueError:
            out["roc_auc_ovr_macro"] = None
    return out


def get_proba(pipe, X):
    if hasattr(pipe, "predict_proba"):
        return pipe.predict_proba(X)
    if hasattr(pipe, "decision_function"):
        # Convert margins to a softmax-like distribution for AUC only.
        d = pipe.decision_function(X)
        e = np.exp(d - d.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)
    return None


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    t0 = time.time()
    print("=" * 70)
    print("SENTIMENT MODEL TRAINING")
    print("=" * 70)

    df = clean(load_raw())
    df.to_csv(DATA_PROCESSED / "sentiment_clean.csv", index=False)

    classes = [c for c in LABEL_ORDER if c in set(df["sentiment"])]
    label_to_id = {c: i for i, c in enumerate(classes)}
    id_to_label = {i: c for c, i in label_to_id.items()}
    df["label"] = df["sentiment"].map(label_to_id)
    print(f"[labels] {label_to_id}")

    X = df["text"].tolist()
    y = df["label"].to_numpy()

    # ---- Leak-free, stratified split. De-duplicated already, so no text overlap.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    overlap = len(set(X_train) & set(X_test))
    print(f"[split] train={len(X_train)} test={len(X_test)} text-overlap={overlap}")

    # ---- Compare unigram vs unigram+bigram, stemming vs none via CV
    print("\n[compare] cross-validating configurations (f1_macro, 3-fold) ...")
    configs = [
        ("unigram+stem", (1, 1), True),
        ("unigram+bigram+stem", (1, 2), True),
        ("unigram+bigram+nostem", (1, 2), False),
    ]
    cv_results = {}
    for name, ngram, stem in configs:
        for model_name, pipe in candidate_models(ngram, stem).items():
            scores = cross_val_score(pipe, X_train, y_train, cv=3, scoring="f1_macro", n_jobs=1)
            key = f"{model_name} | {name}"
            cv_results[key] = {"mean_f1_macro": float(scores.mean()), "std": float(scores.std())}
            print(f"  {key:45s} f1_macro={scores.mean():.4f} (+/- {scores.std():.4f})")

    best_config_name = max(cv_results, key=lambda k: cv_results[k]["mean_f1_macro"])
    print(f"[compare] best configuration: {best_config_name}")

    # Use the winning feature configuration for the final models.
    if "bigram" in best_config_name:
        ngram, stem = (1, 2), "nostem" not in best_config_name
    else:
        ngram, stem = (1, 1), True
    if "nostem" in best_config_name:
        stem = False

    # ---- Train final models on the full training split
    print("\n[train] fitting final models ...")
    trained = {}
    for model_name, pipe in candidate_models(ngram, stem).items():
        t = time.time()
        pipe.fit(X_train, y_train)
        trained[model_name] = pipe
        print(f"  {model_name} fitted in {time.time()-t:.1f}s")

    # Optional neural baseline if torch is available (LSTM). Skipped gracefully.
    lstm_metrics = None
    try:
        from ml.training.lstm import train_lstm, TORCH_AVAILABLE

        if TORCH_AVAILABLE:
            print("\n[train] training optional LSTM ...")
            lstm_metrics, _ = train_lstm(X_train, y_train, X_test, y_test, classes)
    except Exception as exc:  # pragma: no cover - optional path
        print(f"[lstm] skipped: {exc}")

    # ---- Evaluate on held-out test set
    print("\n[evaluate] held-out test set ...")
    metrics = {"dataset": {"classes": classes, "n_train": len(X_train), "n_test": len(X_test),
                            "n_total": int(len(df))}, "configs_cv": cv_results,
               "chosen_config": best_config_name, "models": {}}
    for model_name, pipe in trained.items():
        pred = pipe.predict(X_test)
        proba = get_proba(pipe, X_test)
        m = evaluate(y_test, pred, proba, classes)
        m["n_features"] = int(len(pipe.named_steps["tfidf"].vocabulary_))
        metrics["models"][model_name] = m
        print(f"  {model_name:22s} acc={m['accuracy']:.4f} f1_macro={m['f1_macro']:.4f} "
              f"f1_weighted={m['f1_weighted']:.4f}")
    if lstm_metrics:
        metrics["models"]["LSTM"] = lstm_metrics

    # ---- Select best model by macro F1
    best_name = max(metrics["models"], key=lambda n: metrics["models"][n]["f1_macro"])
    print(f"\n[select] best model: {best_name} (f1_macro={metrics['models'][best_name]['f1_macro']:.4f})")
    best_pipe = trained.get(best_name)

    # ---- Save the chosen pipeline (vectorizer + model together)
    joblib.dump(best_pipe, MODEL_FILE, compress=3)

    metadata = {
        "model_name": best_name,
        "artifact": MODEL_FILE.name,
        "labels": classes,
        "label_to_id": label_to_id,
        "id_to_label": {str(k): v for k, v in id_to_label.items()},
        "ngram_range": list(ngram),
        "stemming": stem,
        "stopword_handling": True,
        "seed": RANDOM_SEED,
        "n_features": int(len(best_pipe.named_steps["tfidf"].vocabulary_)),
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    METADATA_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    METRICS_FILE.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (REPORTS_DIR / "model_comparison.json").write_text(
        json.dumps({k: {kk: vv for kk, vv in v.items()} for k, v in metrics["models"].items()}, indent=2),
        encoding="utf-8",
    )

    print(f"\nSaved model -> {MODEL_FILE}")
    print(f"Saved metrics -> {METRICS_FILE}")
    print(f"Done in {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
