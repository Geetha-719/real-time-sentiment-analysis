"""URL analysis routes: scrape a webpage and predict its sentiment."""
from __future__ import annotations

import json
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import UrlAnalysis, User
from app.schemas import (
    AnalyzeUrlRequest,
    AnalyzeUrlResponse,
    MessageResponse,
    UrlAnalysisOut,
)
from app.scraping.scraper import ScrapeError
from app.services import ml_service, scraping_service

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze-url", response_model=AnalyzeUrlResponse)
def analyze_url(
    payload: AnalyzeUrlRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Fetch the given URL, extract its text and predict sentiment.

    Flow: URL -> requests.get -> BeautifulSoup -> text -> preprocessing ->
    saved TF-IDF -> Logistic Regression -> aggregated sentiment.
    """
    if not ml_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The sentiment model is not available yet. Please try again shortly.",
        )

    try:
        result = scraping_service.analyze_url(payload.url)
    except ScrapeError as exc:
        # Friendly, user-safe message with a sensible HTTP status.
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception:
        # Never leak a stack trace to the user.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The webpage could not be analyzed right now. Please try again.",
        )

    record = UrlAnalysis(
        user_id=current.id,
        url=result["url"],
        title=result["title"][:2000],
        overall_sentiment=result["overall_sentiment"],
        confidence=result["confidence"],
        word_count=result["word_count"],
        chunks_analyzed=result["chunks_analyzed"],
        sentiment_distribution=json.dumps(result["sentiment_distribution"]),
        mean_class_scores=json.dumps(result["mean_class_scores"]),
        preview=result["preview"],
        note=result["note"],
        model_name=ml_service.model_info().get("model_name") or "unknown",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return AnalyzeUrlResponse(
        id=record.id,
        url=record.url,
        final_url=result["final_url"],
        title=record.title,
        overall_sentiment=record.overall_sentiment,
        confidence=record.confidence,
        word_count=record.word_count,
        chunks_analyzed=record.chunks_analyzed,
        sentiment_distribution=result["sentiment_distribution"],
        mean_class_scores=result["mean_class_scores"],
        preview=record.preview,
        note=record.note,
        model_name=record.model_name,
        created_at=record.created_at,
    )


@router.get("/url-history", response_model=dict)
def url_history(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sentiment: str | None = Query(None),
    search: str | None = Query(None),
):
    """Paginated, user-isolated history of URL analyses."""
    filters = [UrlAnalysis.user_id == current.id]
    if sentiment:
        filters.append(UrlAnalysis.overall_sentiment == sentiment)
    if search:
        filters.append(UrlAnalysis.url.ilike(f"%{search}%"))

    total = db.execute(select(func.count(UrlAnalysis.id)).where(*filters)).scalar() or 0
    rows = (
        db.execute(
            select(UrlAnalysis)
            .where(*filters)
            .order_by(UrlAnalysis.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return {
        "items": [UrlAnalysisOut.model_validate(r) for r in rows],
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "pages": max(1, math.ceil(total / page_size)),
    }


@router.get("/url-history/{analysis_id}", response_model=UrlAnalysisOut)
def get_url_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    row = db.execute(
        select(UrlAnalysis).where(
            UrlAnalysis.id == analysis_id, UrlAnalysis.user_id == current.id
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
    return row


@router.delete("/url-history/{analysis_id}", response_model=MessageResponse)
def delete_url_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    row = db.execute(
        select(UrlAnalysis).where(
            UrlAnalysis.id == analysis_id, UrlAnalysis.user_id == current.id
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
    db.execute(delete(UrlAnalysis).where(UrlAnalysis.id == analysis_id, UrlAnalysis.user_id == current.id))
    db.commit()
    return MessageResponse(message="Analysis deleted.")
