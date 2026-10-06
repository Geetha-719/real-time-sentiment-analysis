"""Dashboard, profile and model-insights routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.dashboard import model_insights, user_stats, user_trend
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Prediction, UrlAnalysis, User
from app.schemas import (
    DashboardOut,
    ModelPerformanceOut,
    ProfileOut,
    ProfileUpdate,
    SentimentCount,
    UrlAnalysisOut,
)

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    stats = user_stats(db, current.id)
    recent_rows = (
        db.execute(
            select(UrlAnalysis)
            .where(UrlAnalysis.user_id == current.id)
            .order_by(UrlAnalysis.created_at.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )
    text_analyses = db.execute(
        select(func.count(Prediction.id)).where(Prediction.user_id == current.id)
    ).scalar() or 0
    distribution = [
        SentimentCount(label="Positive", count=stats["positive"]),
        SentimentCount(label="Negative", count=stats["negative"]),
        SentimentCount(label="Neutral", count=stats["neutral"]),
        SentimentCount(label="Irrelevant", count=stats["irrelevant"]),
    ]
    return DashboardOut(
        total_analyses=stats["total_analyses"],
        positive=stats["positive"],
        negative=stats["negative"],
        neutral=stats["neutral"],
        irrelevant=stats["irrelevant"],
        avg_confidence=stats["avg_confidence"],
        total_words=stats["total_words"],
        recent=[UrlAnalysisOut.model_validate(r) for r in recent_rows],
        trend=user_trend(db, current.id, days=14),
        text_analyses=int(text_analyses),
        distribution=distribution,
    )


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    total = db.execute(
        select(func.count(UrlAnalysis.id)).where(UrlAnalysis.user_id == current.id)
    ).scalar() or 0
    return ProfileOut(
        id=current.id,
        full_name=current.full_name,
        email=current.email,
        created_at=current.created_at,
        total_analyses=int(total),
    )


@router.put("/profile", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    current.full_name = payload.full_name
    db.commit()
    db.refresh(current)
    total = db.execute(
        select(func.count(UrlAnalysis.id)).where(UrlAnalysis.user_id == current.id)
    ).scalar() or 0
    return ProfileOut(
        id=current.id,
        full_name=current.full_name,
        email=current.email,
        created_at=current.created_at,
        total_analyses=int(total),
    )


@router.get("/model-performance", response_model=ModelPerformanceOut)
def model_performance():
    insights = model_insights()
    return ModelPerformanceOut(
        available=insights.get("available", False),
        metadata=insights.get("metadata", {}),
        models=insights.get("models", {}),
        dataset=insights.get("dataset", {}),
        top_terms=insights.get("top_terms", {}),
    )
