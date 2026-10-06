"""Model loading, real-time prediction and explainability.

The model is loaded ONCE (module-level singleton) and reused for every
prediction - we never retrain per request.
"""
from __future__ import annotations

import json
import threading
from typing import Iterable

import joblib
import numpy as np
from scipy import sparse

from ml.config import METADATA_FILE, METRICS_FILE, MODEL_FILE

_LOCK = threading.Lock()
_STATE: dict = {}


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load() -> dict:
    """Load the pipeline + metadata + metrics once (thread-safe)."""
    if _STATE:
        return _STATE
    with _LOCK:
        if _STATE:
            return _STATE
        if not MODEL_FILE.exists():
            raise FileNotFoundError(
                f"Model artifact not found at {MODEL_FILE}. Run: python -m ml.training.train"
            )
        pipe = joblib.load(MODEL_FILE)
        metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8")) if METADATA_FILE.exists() else {}
        metrics = json.loads(METRICS_FILE.read_text(encoding="utf-8")) if METRICS_FILE.exists() else {}
        vectorizer = pipe.named_steps["tfidf"]
        classifier = pipe.named_steps["clf"]
        # Prefer human-readable labels from metadata; classifier.classes_ are ints.
        raw_classes = list(getattr(classifier, "classes_", []))
        meta_labels = metadata.get("labels") if metadata else None
        if meta_labels and len(meta_labels) == len(raw_classes) and raw_classes == list(range(len(raw_classes))):
            classes = [str(c) for c in meta_labels]
        else:
            classes = [str(c) for c in raw_classes]
        _STATE.update(
            pipe=pipe,
            vectorizer=vectorizer,
            classifier=classifier,
            metadata=metadata,
            metrics=metrics,
            feature_names=np.asarray(vectorizer.get_feature_names_out()),
            classes=classes,
        )
        return _STATE


def is_ready() -> bool:
    return MODEL_FILE.exists()


def model_info() -> dict:
    state = load()
    return {
        "model_name": state["metadata"].get("model_name"),
        "labels": state["metadata"].get("labels", []),
        "n_features": state["metadata"].get("n_features"),
        "ngram_range": state["metadata"].get("ngram_range"),
        "stemming": state["metadata"].get("stemming"),
        "trained_at": state["metadata"].get("trained_at"),
    }


# --------------------------------------------------------------------------- #
# Explainability
# --------------------------------------------------------------------------- #
def _linear_contributions(vec_row, classifier, class_index: int):
    """Return {feature_index: contribution} for a linear classifier."""
    # vec_row is a 1 x n_features sparse matrix
    coef = classifier.coef_
    if coef.ndim == 1:
        weights = coef
    else:
        weights = coef[class_index]
    nz_idx = vec_row.indices
    nz_val = vec_row.data
    contrib = weights[nz_idx] * nz_val
    return nz_idx, contrib


def _nb_contributions(vec_row, classifier, class_index: int):
    nz_idx = vec_row.indices
    nz_val = vec_row.data
    log_prob = classifier.feature_log_prob_[class_index]
    mean_log_prob = classifier.feature_log_prob_.mean(axis=0)
    contrib = (log_prob[nz_idx] - mean_log_prob[nz_idx]) * nz_val
    return nz_idx, contrib


def _explain(text: str, class_index: int, top_k: int = 8) -> dict:
    state = load()
    vectorizer = state["vectorizer"]
    classifier = state["classifier"]
    feature_names = state["feature_names"]

    vec_row = vectorizer.transform([text])
    if vec_row.nnz == 0:
        return {"influential_terms": [], "top_positive": [], "top_negative": []}

    if hasattr(classifier, "coef_"):
        nz_idx, contrib = _linear_contributions(vec_row, classifier, class_index)
    else:
        nz_idx, contrib = _nb_contributions(vec_row, classifier, class_index)

    order = np.argsort(contrib)
    negative = [(feature_names[nz_idx[i]], float(contrib[i])) for i in order[:top_k] if contrib[i] < 0]
    positive = [(feature_names[nz_idx[i]], float(contrib[i])) for i in order[::-1][:top_k] if contrib[i] > 0]

    influential = []
    for name, w in positive:
        influential.append({"term": name, "weight": round(abs(w), 5), "direction": "supports"})
    for name, w in negative:
        influential.append({"term": name, "weight": round(abs(w), 5), "direction": "opposes"})
    influential.sort(key=lambda d: d["weight"], reverse=True)

    return {
        "influential_terms": influential[:top_k],
        "top_positive": [t for t, _ in positive[:top_k]],
        "top_negative": [t for t, _ in negative[:top_k]],
    }


def _simple_explanation(label: str, top_positive: list[str], top_negative: list[str], confident: bool) -> str:
    """Human-friendly, model-derived explanation (never hardcoded per result)."""
    label_lower = label.lower()
    tone = "confident" if confident else "fairly confident"
    if label in ("Positive",):
        base = f"The model found language patterns commonly associated with positive sentiment and is {tone} about this result."
    elif label == "Negative":
        base = f"The model found language patterns commonly associated with negative sentiment and is {tone} about this result."
    elif label == "Neutral":
        base = f"The model found mostly factual or mixed language with no strong emotion, and is {tone} about this result."
    elif label == "Irrelevant":
        base = f"The text did not contain clear opinion signals about the topic, and the model is {tone} about this result."
    else:
        base = f"The model predicts {label_lower} and is {tone} about this result."

    signals = top_positive[:3] if label in ("Positive",) else top_negative[:3]
    if not signals:
        signals = (top_positive + top_negative)[:3]
    if signals:
        quoted = ", ".join(f"'{s}'" for s in signals)
        base += f" Words such as {quoted} pushed the decision in this direction."
    return base


# --------------------------------------------------------------------------- #
# Prediction
# --------------------------------------------------------------------------- #
def predict(text: str, *, save_details: bool = True) -> dict:
    state = load()
    pipe = state["pipe"]
    classes = state["classes"]

    if text is None or not str(text).strip():
        raise ValueError("Text must not be empty.")

    clean = str(text).strip()
    proba = pipe.predict_proba([clean])[0]
    pred_idx = int(np.argmax(proba))
    pred_label = classes[pred_idx]
    confidence = float(proba[pred_idx])

    class_scores = {classes[i]: round(float(proba[i]), 5) for i in range(len(classes))}

    technical = {"model_name": state["metadata"].get("model_name"), "class_scores": class_scores}
    simple = _simple_explanation(pred_label, [], [], confidence >= 0.6)

    if save_details:
        expl = _explain(clean, pred_idx)
        top_pos, top_neg = expl["top_positive"], expl["top_negative"]
        simple = _simple_explanation(pred_label, top_pos, top_neg, confidence >= 0.6)
        technical.update(
            influential_terms=expl["influential_terms"],
            top_positive_terms=top_pos,
            top_negative_terms=top_neg,
            ngram_range=state["metadata"].get("ngram_range"),
            stemming=state["metadata"].get("stemming"),
        )

    return {
        "text": clean,
        "prediction": pred_label,
        "confidence": round(confidence, 5),
        "class_scores": class_scores,
        "model_name": state["metadata"].get("model_name"),
        "simple_explanation": simple,
        "technical_details": technical,
    }


def predict_batch(texts: Iterable[str]) -> list[dict]:
    """Batch prediction for live/streaming data (chunked to bound memory)."""
    state = load()
    pipe = state["pipe"]
    classes = state["classes"]
    text_list = [str(t).strip() for t in texts]
    results: list[dict] = []
    chunk = 256
    for start in range(0, len(text_list), chunk):
        batch = text_list[start : start + chunk]
        probas = pipe.predict_proba(batch)
        for txt, proba in zip(batch, probas):
            idx = int(np.argmax(proba))
            results.append(
                {
                    "text": txt,
                    "prediction": classes[idx],
                    "confidence": round(float(proba[idx]), 5),
                    "class_scores": {classes[i]: round(float(proba[i]), 5) for i in range(len(classes))},
                }
            )
    return results


def top_terms_by_class(top_k: int = 15) -> dict:
    """Most influential terms per class from the actual model coefficients."""
    state = load()
    classifier = state["classifier"]
    feature_names = state["feature_names"]
    classes = state["classes"]
    out: dict[str, list[str]] = {}
    if hasattr(classifier, "coef_"):
        coef = classifier.coef_
        # For binary, coef_ may be 1-D
        if coef.ndim == 1:
            coef = np.vstack([-coef, coef])
        for i, cls in enumerate(classes):
            idx = np.argsort(coef[i])[::-1][:top_k]
            out[cls] = [str(feature_names[j]) for j in idx]
    else:
        log_prob = classifier.feature_log_prob_
        for i, cls in enumerate(classes):
            idx = np.argsort(log_prob[i])[::-1][:top_k]
            out[cls] = [str(feature_names[j]) for j in idx]
    return out
