"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Make the project root importable so `app` and `ml` packages resolve.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.routes import analyze, auth, dashboard, sentiment  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up / load the ML model once at startup.
    try:
        from app.services import ml_service

        if ml_service.is_ready():
            info = ml_service.model_info()
            logger.info("ML model loaded: %s (%s features)", info.get("model_name"), info.get("n_features"))
        else:
            logger.warning("ML model artifact not found. Train it with: python -m ml.training.train")
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to load ML model: %s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Real-Time Sentiment Analysis System with Web Scraping",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our side. Please try again."},
    )


@app.get("/api/health", tags=["meta"])
def health():
    from app.services import ml_service

    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "model_ready": ml_service.is_ready(),
    }


app.include_router(auth.router)
app.include_router(sentiment.router)
app.include_router(dashboard.router)
app.include_router(analyze.router)
