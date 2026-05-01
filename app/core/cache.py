"""Redis 기반 캐시 데코레이터."""
from __future__ import annotations
import hashlib
import json
from functools import wraps
from typing import Callable
import redis.asyncio as aioredis
from app.config import settings

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def cache_result(ttl: int = 300, prefix: str = "tool"):
    """비동기 함수 결과를 Redis에 캐싱.

    캐시 키: {prefix}:{func_name}:{sha1(json(args+kwargs))}
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
                await r.set(cache_key, json.dumps(result, default=str), ex=ttl)
            except Exception:
                pass
            return result
        return wrapper
    return decorator
