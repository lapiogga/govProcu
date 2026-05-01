"""이메일 디스패처 (SMTP).

환경변수:
    SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM (발신자), SMTP_USE_TLS (default true)
"""
from __future__ import annotations
import asyncio
import os
import smtplib
from email.message import EmailMessage


async def send_email(to: str, subject: str, body: str) -> None:
    """비동기 wrapper — smtplib는 sync, 별도 thread에서 실행."""
    await asyncio.to_thread(_send_sync, to, subject, body)


def _send_sync(to: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")
    if not host:
        raise RuntimeError("SMTP_HOST 미설정")

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    pwd = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", user or "noreply@govprocu")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls()
        if user and pwd:
            smtp.login(user, pwd)
        smtp.send_message(msg)
