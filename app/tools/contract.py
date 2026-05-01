"""계약과정통합공개 영역 MCP 도구.

서비스: 조달청_나라장터 계약과정통합공개서비스 (data.go.kr 15129459)
Base URL: https://apis.data.go.kr/1230000/ao/CntrctProcssIntgOpenService
인증: G2B_KEY_CONTRACT (Encoding 키)

특이사항 (Charlie Research 5/2):
- base path는 /ad가 아닌 /ao
- 본 서비스는 단일 입찰의 계약 진행과정 추적용 (사전규격→공고→낙찰→계약 통합)
- 체결계약 목록·변경계약 이력은 별개 서비스 "계약정보서비스"(15129427) 필요 — 사용자 미신청
- 업무유형 4종: Thng(물품)/Cnstwk(공사)/Servc(용역)/Frgcpt(외자)

도구:
- get_contract_process: 한 입찰의 계약 진행과정 (실 구현)
- get_contract_detail: 단건 상세 (실 구현 — get_contract_process와 거의 동일, items[0])
- search_contracts: 별개 키 필요 (스텁 유지)
- list_contract_changes: 별개 키 필요 (스텁 유지)
"""
from __future__ import annotations
from app.clients.g2b import G2BClient
from app.config import settings
from app.core.cache import cache_result
from app.core.rate_limit import check_rate


_PROCESS_BASE = "/CntrctProcssIntgOpenService/getCntrctProcssIntgOpenInfo"
_PROCESS_ENDPOINTS = {
    "Cnstwk": _PROCESS_BASE + "Cnstwk",
    "Servc": _PROCESS_BASE + "Servc",
    "Thng": _PROCESS_BASE + "Thng",
    "Frgcpt": _PROCESS_BASE + "Frgcpt",
}


def _extract_items(body: dict) -> list[dict]:
    items = body.get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    if not isinstance(items, list):
        items = [items] if items else []
    return items


@cache_result(ttl=settings.cache_ttl_short, prefix="contract_process")
async def get_contract_process(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """공고번호 기준 계약과정(사전규격→공고→낙찰→계약) 통합 정보 조회.

    Charlie Research: inqryDiv=4 + bidNtceNo로 단건 조회. 4종 endpoint 자동 시도.

    Args:
        bid_notice_no: 입찰공고번호
        bid_ord: 차수 (기본 "00")
    """
    allowed, remaining = await check_rate("g2b_contract", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_contract 토큰 소진 (remaining={remaining})")

    client = G2BClient(base_url=settings.g2b_contract_base_url)
    try:
        for biz_div, endpoint in _PROCESS_ENDPOINTS.items():
            params = {
                "pageNo": 1,
                "numOfRows": 10,
                "inqryDiv": "4",
                "bidNtceNo": bid_notice_no,
                "bidNtceOrd": bid_ord,
            }
            try:
                body = await client.call(endpoint, settings.g2b_key_contract, params)
            except Exception:
                continue
            items = _extract_items(body)
            if items:
                return {
                    "found": True,
                    "biz_div": biz_div,
                    "endpoint": endpoint,
                    "bid_notice_no": bid_notice_no,
                    "bid_ord": bid_ord,
                    "items": items,
                    "count": len(items),
                }
        return {
            "found": False,
            "bid_notice_no": bid_notice_no,
            "bid_ord": bid_ord,
            "note": "계약과정 4종 endpoint 모두 미발견. 공고번호·차수 확인 또는 아직 계약 미체결.",
        }
    finally:
        await client.aclose()


async def get_contract_detail(
    bid_notice_no: str | None = None,
    bid_ord: str = "00",
    contract_no: str | None = None,
) -> dict:
    """계약 단건 상세 조회.

    본 서비스는 별도 단건 endpoint가 없음 → get_contract_process의 첫 항목을 사용.
    contract_no 파라미터는 향후 계약정보서비스(15129427) 통합 시 사용.
    """
    if not bid_notice_no:
        return {
            "status": "missing_input",
            "note": "bid_notice_no 필수. contract_no 단독 조회는 계약정보서비스(별도 키) 필요.",
        }
    process = await get_contract_process(bid_notice_no, bid_ord)
    if process.get("found"):
        items = process.get("items", [])
        return {
            "found": True,
            "endpoint": process.get("endpoint"),
            "biz_div": process.get("biz_div"),
            "bid_notice_no": bid_notice_no,
            "bid_ord": bid_ord,
            "detail": items[0] if items else None,
        }
    return process


# === 별개 키 필요 (스텁 유지) ===

async def search_contracts(
    inst_code: str | None = None,
    inst_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
) -> dict:
    """기간/기관/업종/키워드 기준 체결 계약 목록 조회 (스텁).

    별개 서비스 "계약정보서비스"(data.go.kr 15129427) 키 필요.
    현재 G2B_KEY_CONTRACT는 계약과정통합공개서비스용으로 호출 불가.
    """
    return {
        "status": "not_implemented",
        "domain": "contract",
        "tool": "search_contracts",
        "items": [],
        "total_count": 0,
        "note": "별개 서비스 '계약정보서비스(15129427)' 키 신청 필요. 현재 G2B_KEY_CONTRACT는 계약과정통합공개용.",
    }


async def list_contract_changes(
    contract_no: str | None = None,
    bid_notice_no: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """변경 계약 이력 조회 (스텁).

    별개 서비스 "계약정보서비스" 키 필요.
    """
    return {
        "status": "not_implemented",
        "domain": "contract",
        "tool": "list_contract_changes",
        "items": [],
        "note": "별개 서비스 '계약정보서비스(15129427)' 키 신청 필요.",
    }
