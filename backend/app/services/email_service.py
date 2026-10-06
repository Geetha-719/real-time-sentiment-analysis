"""Transactional email helper.

If SMTP is not configured, the reset link is logged and (in development)
returned to the caller so the flow remains testable without a mail server.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger("app.email")


def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    """Return True if an email was actually sent via SMTP."""
    subject = "Reset your password"
    body = (
        "Someone requested a password reset for your account.\n\n"
        f"Reset your password using this link (valid for {settings.password_reset_expire_minutes} minutes):\n"
        f"{reset_link}\n\n"
        "If you did not request this, you can safely ignore this email."
    )

    if not settings.smtp_host:
        logger.warning("[email] SMTP not configured. Password reset link for %s: %s", to_email, reset_link)
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error("[email] Failed to send reset email: %s", exc)
        return False
