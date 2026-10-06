"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ----------------------------- Auth ---------------------------------------- #
class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split()).strip()
        if len(v) < 2:
            raise ValueError("Full name is too short.")
        return v

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one letter and one number.")
        return v

    def model_post_init(self, __context) -> None:  # noqa: D401
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    # Only populated in development when SMTP is not configured.
    reset_link: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one letter and one number.")
        return v

    def model_post_init(self, __context) -> None:  # noqa: D401
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")


class MessageResponse(BaseModel):
    message: str


# --------------------------- Predictions ----------------------------------- #
class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Text must not be empty.")
        return v.strip()


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str
    prediction: str
    confidence: float
    model_name: str
    simple_explanation: str
    technical_explanation: str
    created_at: datetime


class PredictResponse(PredictionOut):
    class_scores: dict[str, float] = {}


class PredictionListResponse(BaseModel):
    items: list[PredictionOut]
    total: int
    page: int
    page_size: int
    pages: int


# ----------------------------- Profile ------------------------------------- #
class ProfileOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    created_at: datetime
    total_analyses: int


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)


# ---------------------------- URL analysis --------------------------------- #
class AnalyzeUrlRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)

    @field_validator("url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Please enter a webpage URL.")
        return v


class UrlAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    title: str
    overall_sentiment: str
    confidence: float
    word_count: int
    chunks_analyzed: int
    sentiment_distribution: dict[str, float] = {}
    preview: str = ""
    note: str = ""
    model_name: str = ""
    created_at: datetime

    @field_validator("sentiment_distribution", mode="before")
    @classmethod
    def parse_distribution(cls, v):
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}


class AnalyzeUrlResponse(BaseModel):
    id: int | None = None
    url: str
    final_url: str
    title: str
    overall_sentiment: str
    confidence: float
    word_count: int
    chunks_analyzed: int
    sentiment_distribution: dict[str, float]
    mean_class_scores: dict[str, float] = {}
    preview: str
    note: str = ""
    model_name: str = ""
    created_at: datetime | None = None


# ----------------------------- Dashboard ----------------------------------- #
class SentimentCount(BaseModel):
    label: str
    count: int


class DashboardOut(BaseModel):
    total_analyses: int
    positive: int
    negative: int
    neutral: int
    irrelevant: int
    avg_confidence: float
    total_words: int
    recent: list[UrlAnalysisOut]
    trend: list[dict]
    text_analyses: int
    distribution: list[SentimentCount]


# --------------------------- Model insights -------------------------------- #
class ModelPerformanceOut(BaseModel):
    available: bool
    metadata: dict
    models: dict
    dataset: dict
    top_terms: dict
