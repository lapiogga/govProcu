"""bid 도구 단위 테스트 (G2B 호출 mock)."""
import pytest
from unittest.mock import AsyncMock, patch
from app.tools.bid import search_bid_notices, _normalize_notice


def test_normalize_notice_basic():
    raw = {
        "bidNtceNo": "20260100123",
        "bidNtceOrd": "00",
        "bidNtceNm": "정보화 용역",
        "ntceInsttNm": "조달청",
        "presmptPrce": "1,500,000,000",
        "bidNtceDt": "2026-04-01",
    }
    n = _normalize_notice(raw)
    assert n.bid_no == "20260100123"
    assert n.title == "정보화 용역"
    assert n.estimated_price == 1_500_000_000


@pytest.mark.asyncio
async def test_search_bid_notices_returns_dict_shape():
    """G2B 호출을 mock하고 반환 형태만 검증."""
    fake_body = {"items": {"item": [
        {"bidNtceNo": "1", "bidNtceNm": "test", "ntceInsttNm": "기관", "presmptPrce": "100"},
    ]}, "totalCount": 1}

    with patch("app.tools.bid.G2BClient") as MockClient:
        instance = MockClient.return_value
        instance.call = AsyncMock(return_value=fake_body)
        instance.aclose = AsyncMock()

        # 캐시·rate_limit 우회
        with patch("app.tools.bid.check_rate", new=AsyncMock(return_value=(True, 9))), \
             patch("app.tools.bid.cache_result", lambda **k: (lambda fn: fn)):
            from app.tools import bid as bid_mod
            from importlib import reload
            reload(bid_mod)  # 데코레이터 재적용
            result = await bid_mod.search_bid_notices(keyword="test", limit=5)

    assert "items" in result
    assert result["total_count"] == 1
    assert result["returned_count"] == 1
    assert result["has_more"] is False
