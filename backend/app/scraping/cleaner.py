"""Cleanup and sentence chunking for scraped webpage text."""
from __future__ import annotations

import re

# Common boilerplate fragments that add noise but no sentiment.
_BOILERPLATE = [
    r"cookie[s]? (policy|settings|preferences).*$",
    r"accept all cookies.*$",
    r"subscribe (now|today|to).*$",
    r"sign up (for|to).*$",
    r"all rights reserved.*$",
    r"share this (article|story|page).*$",
    r"advertisement\s*$",
    r"read more.*$",
    r"click here.*$",
]
_BOILER_RE = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in _BOILERPLATE]

_WS_RE = re.compile(r"[ \t\r\f\v]+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def clean_scraped_text(text: str) -> str:
    """Remove boilerplate lines and normalize whitespace."""
    if not text:
        return ""
    text = _WS_RE.sub(" ", text)
    for rx in _BOILER_RE:
        text = rx.sub("", text)
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln).strip()


def split_into_chunks(
    text: str,
    *,
    max_chars: int = 400,
    min_word_count: int = 4,
) -> list[str]:
    """Split text into sentence-ish chunks suitable for per-chunk prediction.

    The dataset used for training is short (tweets), so classifying a whole
    webpage at once would mismatch the training distribution. Instead we split
    the page into short chunks and aggregate their predictions.
    """
    text = clean_scraped_text(text)
    if not text:
        return []

    # Split on sentence boundaries and newlines.
    raw_sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text)]

    chunks: list[str] = []
    buffer = ""
    for sentence in raw_sentences:
        if not sentence:
            continue
        candidate = f"{buffer} {sentence}".strip() if buffer else sentence
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            if buffer:
                chunks.append(buffer)
            buffer = sentence if len(sentence) <= max_chars else sentence[:max_chars]
    if buffer:
        chunks.append(buffer)

    # Keep only chunks with enough words to carry a signal.
    return [c for c in chunks if len(c.split()) >= min_word_count]
