"""Thin wrapper around the ML inference layer.

Keeps the model loaded as a process singleton (see ml.inference) and exposes
predict / predict_batch / metadata to the API.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root (which contains the `ml` package) is importable.
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml import inference as _inference  # noqa: E402


def is_ready() -> bool:
    return _inference.is_ready()


def model_info() -> dict:
    return _inference.model_info()


def predict(text: str) -> dict:
    return _inference.predict(text)


def predict_batch(texts: list[str]) -> list[dict]:
    return _inference.predict_batch(texts)


def metadata() -> dict:
    _inference.load()
    return _inference._STATE["metadata"]


def metrics() -> dict:
    _inference.load()
    return _inference._STATE["metrics"]


def top_terms_by_class(top_k: int = 15) -> dict:
    return _inference.top_terms_by_class(top_k=top_k)
