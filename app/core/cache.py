"""Redis 기반 캐시 데코레이터."""
from __future__ import annotations
import hashlib
import json
from functools import wraps
from typing import Any, Callable
import redis.asyncio as aioredis
from app.config import settings

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _is_empty_result(result: Any) -> bool:
    """v29.1.3 (F11 P3): 빈 응답 판정 — 빈 응답은 짧은 TTL로 캐싱.

    사용자가 키 발급/데이터 재추가 후 30분 동안 stale 응답 받지 않도록.
    """
    if not isinstance(result, dict):
        return False
    # not_implemented stub → empty
    if result.get("status") == "not_implemented":
        return True
    # items list 비어있음 + total 없음 → empty
    items = result.get("items")
    if isinstance(items, list) and len(items) == 0:
        # total_count > 0이지만 매칭 0인 케이스도 empty (false-negative 가능)
        return True
    # workflow류 (sections.*.items 모두 빈) — vendor_profile/agency_bid_summary
    sections = result.get("sections")
    if isinstance(sections, dict) and sections:
        all_empty = True
        for sec in sections.values():
            if not isinstance(sec, dict):
                continue
            sec_items = sec.get("items")
            if isinstance(sec_items, list) and len(sec_items) > 0:
                all_empty = False
                break
            if sec.get("status") and sec.get("status") != "not_implemented":
                # NTS 정상 응답 등 — non-empty
                if sec_items or sec.get("found"):
                    all_empty = False
                    break
        if all_empty:
            return True
    return False


def cache_result(ttl: int = 300, prefix: str = "tool", empty_ttl: int | None = None):
    """비동기 함수 결과를 Redis에 캐싱.

    캐시 키: {prefix}:{func_name}:{sha1(json(args+kwargs))}

    Args:
        ttl: 정상 응답 TTL (초)
        prefix: 캐시 키 prefix
        empty_ttl: 빈 응답 TTL (None이면 ttl 그대로). v29.1.3 — 빈 응답은
                   짧게 캐싱하여 사용자 키 발급/재시도 시 stale 회피.
    """
    def decorator(fn: Callable):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            key_payload = json.dumps({"args": args, "kwargs": kwargs}, default=str, sort_keys=True)
            key_hash = hashlib.sha1(key_payload.encode()).hexdigest()[:16]
            cache_key = f"{prefix}:{fn.__name__}:{key_hash}"
            r = get_redis()
            try:
                cached = await r.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass  # 캐시 장애 시 우회
            result = await fn(*args, **kwargs)
            try:
                actual_ttl = ttl
                if empty_ttl is not None and _is_empty_result(result):
                    actual_ttl = empty_ttl
                await r.set(cache_key, json.dumps(result, default=str), ex=actual_ttl)
            except Exception:
                pass
            return result
        return wrapper
    return decorator
