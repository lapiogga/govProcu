"""G2B API 1개월 제약 대응 — date range 자동 분할 유틸.

G2B 입찰공고/낙찰정보/개찰결과 OpenAPI는 inqryBgnDt~inqryEndDt 최대 1개월 제약.
이를 초과하면 resultCode 07 (입력값 범위 초과) 또는 silent 0건 반환.

본 모듈은 사용자가 1년/5년치를 요청해도 내부적으로 1개월씩 chunking하여 순차 호출
후 결과를 merge할 수 있도록 chunk 생성 유틸을 제공.
"""
from __future__ import annotations

from datetime import datetime, timedelta


_FMT = "%Y%m%d"


def _parse(s: str) -> datetime:
    """YYYYMMDD 또는 YYYY-MM-DD 형식 파싱."""
    s = (s or "").strip().replace("-", "")
    return datetime.strptime(s[:8], _FMT)


def _fmt(d: datetime) -> str:
    return d.strftime(_FMT)


def chunk_date_range(
    date_from: str | None,
    date_to: str | None,
    *,
    max_days: int = 31,
) -> list[tuple[str, str]]:
    """date_from~date_to를 max_days 단위 청크로 분할.

    - 둘 다 None이면 [(None, None)] 한 청크 — caller가 그대로 호출
    - 한쪽만 있으면 [(date_from, date_to)] 그대로 — chunking 불가, 호출 위임
    - 청크 크기는 max_days 일 (default 31일, G2B 1개월 제약 대응)
    - 모든 청크는 YYYYMMDD 문자열 튜플

    예: chunk_date_range("20260101", "20260501", max_days=31)
        → [("20260101","20260131"),("20260201","20260303"),
           ("20260304","20260403"),("20260404","20260501")]
    """
    if not date_from or not date_to:
        return [(date_from, date_to)]

    try:
        start = _parse(date_from)
        end = _parse(date_to)
    except ValueError:
        # 파싱 실패 시 그대로 위임
        return [(date_from, date_to)]

    if start > end:
        return [(date_from, date_to)]

    # 단일 청크에 들어가면 분할 불필요
    span_days = (end - start).days
    if span_days <= max_days:
        return [(_fmt(start), _fmt(end))]

    chunks: list[tuple[str, str]] = []
    cur = start
    delta = timedelta(days=max_days - 1)  # inclusive 범위라 -1
    while cur <= end:
        nxt = min(cur + delta, end)
        chunks.append((_fmt(cur), _fmt(nxt)))
        cur = nxt + timedelta(days=1)
    return chunks


def default_recent_range(days: int = 30) -> tuple[str, str]:
    """오늘 기준 최근 N일 범위 (YYYYMMDD, YYYYMMDD)."""
    today = datetime.now()
    start = today - timedelta(days=days)
    return _fmt(start), _fmt(today)
