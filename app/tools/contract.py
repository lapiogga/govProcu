"""계약과정통합공개 영역 MCP 도구 (스텁 — M5 단계 구현 예정).

조달청 나라장터 계약과정통합공개서비스(G2B_KEY_CONTRACT)를 사용한다.
"""
from __future__ import annotations


async def get_contract_process(bid_no: str, bid_ord: str = "00") -> dict:
    """공고번호 기준 계약과정(공고→낙찰→계약) 통합 정보를 조회합니다. (stub)"""
    raise NotImplementedError("M5 단계 구현 예정")


async def search_contracts(
    inst_code: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 20,
) -> dict:
    """기간/기관/업종으로 계약 목록을 조회합니다. (stub)"""
    raise NotImplementedError("M5 단계 구현 예정")
