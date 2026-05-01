"""Slack incoming webhook.

환경변수:
    SLACK_WEBHOOK_URL — 전역 default. 사용자별 webhook은 인자로 override.
"""
from __future__ import annotations
import os

import httpx


async def send_slack(webhook_url: str | None, text: str) -> None:
    """슬랙 webhook 발송. 4000자 초과 시 잘라냄."""
    url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        raise RuntimeError("SLACK_WEBHOOK_URL 미설정")

    payload = {"text": text[:4000]}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
