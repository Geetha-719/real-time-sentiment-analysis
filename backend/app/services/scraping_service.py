"""High-level URL analysis service.

    analyze_url(url):
        URL -> scrape_url() -> clean -> chunk -> ML pipeline -> aggregate
"""
from __future__ import annotations

import json
from collections import Counter

from app.scraping.cleaner import clean_scraped_text, split_into_chunks
from app.scraping.scraper import ScrapeError, ScrapedPage, scrape_url
from app.services import ml_service

# Keep memory/CPU bounded for very large pages.
MAX_CHUNKS = 300
PREVIEW_CHARS = 600


def _preview(text: str, limit: int = PREVIEW_CHARS) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def analyze_url(url: str, *, respect_robots: bool = True) -> dict:
    """Fetch a webpage, extract its text and return aggregated sentiment.

    Raises ScrapeError for scraping problems. Raises RuntimeError if the model
    is unavailable.
    """
    if not ml_service.is_ready():
        raise RuntimeError("The sentiment model is not available.")

    page: ScrapedPage = scrape_url(url, respect_robots=respect_robots)

    cleaned = clean_scraped_text(page.text)
    chunks = split_into_chunks(cleaned)[:MAX_CHUNKS]

    if not chunks:
        raise ScrapeError(
            "This page did not contain enough readable text to analyze.",
            kind="too_little_text",
        )

    # Real model predictions, one per chunk (batched for speed).
    predictions = ml_service.predict_batch(chunks)

    label_counts: Counter[str] = Counter()
    prob_sums: dict[str, float] = {}
    for pred in predictions:
        label = pred["prediction"]
        label_counts[label] += 1
        for cls, prob in pred["class_scores"].items():
            prob_sums[cls] = prob_sums.get(cls, 0.0) + prob

    n = len(predictions)
    distribution = {
        label: round(100.0 * count / n, 1) for label, count in label_counts.items()
    }
    # Ensure all four labels appear.
    for label in ("Positive", "Negative", "Neutral", "Irrelevant"):
        distribution.setdefault(label, 0.0)

    # Overall = most frequently predicted chunk label (tie-break by mean prob).
    overall = max(
        label_counts,
        key=lambda k: (label_counts[k], prob_sums.get(k, 0.0) / n),
    )

    # Confidence = mean model probability assigned to the overall class.
    confidence = round(prob_sums.get(overall, 0.0) / n, 4)

    # Honest labelling for factual / non-opinionated pages.
    opinion_share = distribution.get("Positive", 0) + distribution.get("Negative", 0)
    note = ""
    if overall in ("Neutral", "Irrelevant") or opinion_share < 30:
        note = (
            "This page appears to be mostly factual or informational, "
            "so it does not express strong sentiment."
        )

    mean_scores = {cls: round(prob_sums.get(cls, 0.0) / n, 4) for cls in prob_sums}

    return {
        "url": page.url,
        "final_url": page.final_url,
        "title": page.title,
        "overall_sentiment": overall,
        "confidence": confidence,
        "word_count": page.word_count,
        "chunks_analyzed": n,
        "sentiment_distribution": distribution,
        "mean_class_scores": mean_scores,
        "preview": _preview(cleaned),
        "note": note,
    }


def result_to_json(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False)
