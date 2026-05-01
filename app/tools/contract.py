"""계약과정통합공개 영역 MCP 도구.

조달청 나라장터 계약과정통합공개서비스(G2B_KEY_CONTRACT)를 사용한다.
입찰 → 낙찰 → 체결 → 변경계약까지 계약 진행 과정을 통합 조회한다.

도구 매트릭스 (REPLAN.md v2):
- get_contract_process: 한 입찰의 계약 진행 과정
- search_contracts: 기간·기관·업종 기준 체결 계약 목록
- list_contract_changes: 변경 계약 이력
- get_contract_detail: 계약 단건 상세
"""
from __future__ import annotations


async def get_contract_process(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """공고번호 기준 계약과정(공고→낙찰→체결→변경) 통합 정보 조회 (스텁).

    Args:
        bid_notice_no: 입찰공고번호
        bid_ord: 차수 (기본 "00")
    """
    return {
        "status": "not_implemented",
        "domain": "contract",
        "tool": "get_contract_process",
        "bid_notice_no": bid_notice_no,
        "bid_ord": bid_ord,
        "note": "계약과정통합공개서비스 매핑 진행 중",
    }


async def search_contracts(
    inst_code: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
) -> dict:
    """기간/기관/업종/키워드로 체결 계약 목록 조회 (스텁)."""
    return {
        "status": "not_implemented",
        "domain": "contract",
        "tool": "search_contracts",
        "items": [],
        "total_count": 0,
        "returned_count": 0,
        "has_more": False,
        "note": "계약과정통합공개서비스 매핑 진행 중",
    }


async def list_contract_changes(
    contract_no: str | None = None,
    bid_notice_no: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """계약번호 또는 공고번호로 변경 계약 이력 조회 (스텁)."""
    return {
        "status": "not_implemented",
        "domain": "contract",
        "tool": "list_contract_changes",
        "items": [],
        "total_count": 0,
        "note": "계약과정통합공개서비스 매핑 진행 중",
    }


async def get_contract_detail(
    contract_no: str | None = None,
    bid_notice_no: str | None = None,
    bid_ord: str = "00",
) -> dict:
    """계약번호 또는 공고번호+차수로 계약 단건 상세 조회 (스텁)."""
    return {
        "status": "not_implemented",
        "domain": "contract",
        "tool": "get_contract_detail",
        "contract_no": contract_no,
        "bid_notice_no": bid_notice_no,
        "bid_ord": bid_ord,
        "note": "계약과정통합공개서비스 매핑 진행 중",
    }
