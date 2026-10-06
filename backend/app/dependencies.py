"""Shared FastAPI dependencies: current user, DB, etc."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your session has expired or is invalid. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not credentials.credentials:
        raise unauthorized
    payload = decode_access_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise unauthorized
    subject = payload.get("sub")
    if subject is None:
        raise unauthorized
    user = db.get(User, int(subject))
    if user is None:
        raise unauthorized
    return user
