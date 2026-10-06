"""Sentiment prediction and prediction-history routes (user-isolated)."""
from __future__ import annotations

import json
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Prediction, User
from app.schemas import (
    MessageResponse,
    PredictRequest,
    PredictionListResponse,
    PredictionOut,
    PredictResponse,
)
from app.services import ml_service

router = APIRouter(prefix="/api", tags=["sentiment"])


@router.post("/sentiment/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if not ml_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The sentiment model is not available yet. Please try again shortly.",
        )
    try:
        result = ml_service.predict(payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The sentiment analysis could not be completed. Please try again.",
        )

    record = Prediction(
        user_id=current.id,
        text=result["text"],
        prediction=result["prediction"],
        confidence=result["confidence"],
        model_name=result["model_name"] or "unknown",
        simple_explanation=result["simple_explanation"],
        technical_explanation=json.dumps(result["technical_details"]),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictResponse(
        id=record.id,
        text=record.text,
        prediction=record.prediction,
        confidence=record.confidence,
        model_name=record.model_name,
        simple_explanation=record.simple_explanation,
        technical_explanation=record.technical_explanation,
        created_at=record.created_at,
        class_scores=result["class_scores"],
    )


@router.get("/predictions", response_model=PredictionListResponse)
def list_predictions(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sentiment: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
):
    """Paginated, user-isolated history with filtering and search."""
    filters = [Prediction.user_id == current.id]
    if sentiment:
        filters.append(Prediction.prediction == sentiment)
    if search:
        filters.append(Prediction.text.ilike(f"%{search}%"))

    total = db.execute(select(func.count(Prediction.id)).where(*filters)).scalar() or 0
    order = Prediction.created_at.desc() if sort == "desc" else Prediction.created_at.asc()
    rows = (
        db.execute(
            select(Prediction)
            .where(*filters)
            .order_by(order)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return PredictionListResponse(
        items=[PredictionOut.model_validate(r) for r in rows],
        total=int(total),
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/predictions/{prediction_id}", response_model=PredictionOut)
def get_prediction(prediction_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    row = db.execute(
        select(Prediction).where(Prediction.id == prediction_id, Prediction.user_id == current.id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found.")
    return row


@router.delete("/predictions/{prediction_id}", response_model=MessageResponse)
def delete_prediction(prediction_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    row = db.execute(
        select(Prediction).where(Prediction.id == prediction_id, Prediction.user_id == current.id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found.")
    db.execute(delete(Prediction).where(Prediction.id == prediction_id, Prediction.user_id == current.id))
    db.commit()
    return MessageResponse(message="Prediction deleted.")
