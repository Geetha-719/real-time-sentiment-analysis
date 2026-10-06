"""Dashboard and trend aggregations for URL analyses (all from real DB data)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import UrlAnalysis
from app.services import ml_service


def user_stats(db: Session, user_id: int) -> dict:
    rows = db.execute(
        select(UrlAnalysis.overall_sentiment, func.count(UrlAnalysis.id))
        .where(UrlAnalysis.user_id == user_id)
        .group_by(UrlAnalysis.overall_sentiment)
    ).all()
    counts = {label: int(c) for label, c in rows}
    total = sum(counts.values())
    avg_conf = db.execute(
        select(func.avg(UrlAnalysis.confidence)).where(UrlAnalysis.user_id == user_id)
    ).scalar()
    total_words = db.execute(
        select(func.coalesce(func.sum(UrlAnalysis.word_count), 0)).where(UrlAnalysis.user_id == user_id)
    ).scalar() or 0
    return {
        "total_analyses": total,
        "positive": counts.get("Positive", 0),
        "negative": counts.get("Negative", 0),
        "neutral": counts.get("Neutral", 0),
        "irrelevant": counts.get("Irrelevant", 0),
        "avg_confidence": round(float(avg_conf), 4) if avg_conf is not None else 0.0,
        "total_words": int(total_words),
    }


def user_trend(db: Session, user_id: int, days: int = 14) -> list[dict]:
    """Daily counts by sentiment for the last `days` days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        select(
            func.date(UrlAnalysis.created_at).label("day"),
            UrlAnalysis.overall_sentiment,
            func.count(UrlAnalysis.id),
        )
        .where(UrlAnalysis.user_id == user_id, UrlAnalysis.created_at >= since)
        .group_by("day", UrlAnalysis.overall_sentiment)
        .order_by("day")
    ).all()

    buckets: dict[str, dict] = {}
    for day, label, count in rows:
        key = str(day)
        b = buckets.setdefault(key, {"date": key, "Positive": 0, "Negative": 0, "Neutral": 0, "Irrelevant": 0})
        b[label] = int(count)
    return list(buckets.values())


def model_insights() -> dict:
    if not ml_service.is_ready():
        return {"available": False, "metadata": {}, "models": {}, "dataset": {}, "top_terms": {}}
    m = ml_service.metrics()
    return {
        "available": True,
        "metadata": ml_service.metadata(),
        "models": m.get("models", {}),
        "dataset": m.get("dataset", {}),
        "configs_cv": m.get("configs_cv", {}),
        "chosen_config": m.get("chosen_config"),
        "top_terms": ml_service.top_terms_by_class(top_k=15),
    }
