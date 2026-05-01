"""토큰 버킷 Rate Limiter (Redis 공유)."""
from __future__ import annotations
import time
from app.core.cache import get_redis


async def check_rate(bucket: str, capacity: int, refill_per_sec: float) -> tuple[bool, int]:
    """토큰 버킷 체크. (허용여부, 잔여토큰) 반환.

    Lua script로 원자적 처리. 다중 인스턴스에서도 정합성 유지.
    """
    r = get_redis()
    now = time.time()
    script = """
    local k = KEYS[1]
    local cap = tonumber(ARGV[1])
    local refill = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    local data = redis.call('HMGET', k, 'tokens', 'ts')
    local tokens = tonumber(data[1]) or cap
    local ts = tonumber(data[2]) or now
    local delta = math.max(0, now - ts)
    tokens = math.min(cap, tokens + delta * refill)
    local allowed = 0
    if tokens >= 1 then
      tokens = tokens - 1
      allowed = 1
    end
    redis.call('HMSET', k, 'tokens', tokens, 'ts', now)
    redis.call('EXPIRE', k, 3600)
    return {allowed, math.floor(tokens)}
    """
    res = await r.eval(script, 1, f"rate:{bucket}", capacity, refill_per_sec, now)
    return bool(res[0]), int(res[1])
