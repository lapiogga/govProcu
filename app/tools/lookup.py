"""lookup 영역 MCP 도구 — Relational Key 기반 cross-lookup.

사용자 5/2 00:48 통찰:
> "공고번호(또는 공고번호+차수), 계약번호, 발주기관코드, 사업자등록번호를
>  서로의 상관관계를 엮어주는 주요한 relational key가 될 것 같음."

4개 핵심 키:
- bid_notice_no (+ bid_ord): 입찰공고번호 — 입찰 한 건의 1차 키
- contract_no: 계약번호 — 체결된 계약의 1차 키
- inst_code: 발주기관코드 — 발주 주체
- vendor_biz_no: 사업자등록번호 — 응찰자/낙찰자 주체

한 키로 시작하면 다른 키들과의 모든 관계를 추적한다.

도구:
- lookup_by_bid_no: 공고번호 → 사전규격·공고·낙찰자(biz_no)·발주기관코드·계약번호
- lookup_by_inst_code: 발주기관 코드 → 최근 발주 목록 + 낙찰업체 분포
- lookup_by_biz_no: 사업자번호 → NTS 진위 + 낙찰 공고번호 목록 + 거래 발주기관 분포
- lookup_by_contract_no: 계약번호 → 공고번호·낙찰자·발주기관 (별개 키 필요로 스텁)
"""
from __future__ import annotations
from collections import Counter
from typing import Any

from app.tools import bid as bid_tools
from app.tools import award as award_tools
from app.tools import contract as contract_tools
from app.tools import vendor as vendor_tools


def _safe_get(d: dict, *keys, default=None):
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


# === 1. lookup_by_bid_no ===

async def lookup_by_bid_no(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """공고번호(+차수)로 시작하여 다른 relational key들을 모두 추적.

    반환 keys: bid_notice_no, bid_ord, inst_code, inst_name, vendor_biz_no, contract_no.
    + 각 단계별 상세(notice/award/contract) 핵심 필드.
    """
    keys: dict[str, Any] = {
        "bid_notice_no": bid_notice_no,
        "bid_ord": bid_ord,
        "inst_code": None,
        "inst_name": None,
        "vendor_biz_no": None,
        "vendor_name": None,
        "contract_no": None,
    }
    sections: dict[str, Any] = {}

    # 공고
    notice = await bid_tools.get_bid_notice_detail(bid_notice_no, bid_ord)
    sections["notice"] = notice
    if notice.get("found"):
        raw = notice.get("raw", {})
        summary = notice.get("summary", {})
        keys["inst_code"] = raw.get("dminsttCd") or raw.get("ntceInsttCd")
        keys["inst_name"] = summary.get("inst_name")

    # 낙찰
    award = await award_tools.get_award_detail(bid_notice_no, bid_ord)
    sections["award"] = award
    if award.get("found"):
        award_summary = award.get("summary", {})
        keys["vendor_biz_no"] = award_summary.get("winner_biz_no")
        keys["vendor_name"] = award_summary.get("winner_name")

    # 계약 과정
    process = await contract_tools.get_contract_process(bid_notice_no, bid_ord)
    sections["contract_process"] = process
    if process.get("found"):
        for item in process.get("items", []) or []:
            cn = item.get("cntrctRefNo") or item.get("cntrctNo") or item.get("cntrctRfrnceNo")
            if cn:
                keys["contract_no"] = cn
                break

    return {
        "starting_key": "bid_notice_no",
        "keys": keys,
        "sections": sections,
    }


# === 2. lookup_by_inst_code ===

async def lookup_by_inst_code(
    inst_code: str | None = None,
    inst_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 30,
) -> dict:
    """발주기관 코드(또는 기관명)로 최근 발주 목록 + 낙찰업체 분포 추적.

    inst_code 또는 inst_name 중 하나는 필수.
    """
    if not (inst_code or inst_name):
        raise ValueError("inst_code 또는 inst_name 중 하나는 필수")

    notices = await bid_tools.search_bid_notices(
        inst_name=inst_name,
        biz_type=biz_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    awards = await award_tools.search_awards(
        inst_name=inst_name,
        biz_type=biz_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )

    award_items = awards.get("items", [])

    # 낙찰업체 분포
    winner_counter: Counter[str] = Counter()
    winner_amounts: dict[str, int] = {}
    winner_names: dict[str, str] = {}
    for row in award_items:
        biz_no = row.get("winner_biz_no")
        if not biz_no:
            continue
        winner_counter[biz_no] += 1
        try:
            amt = int(str(row.get("award_amount", 0)).replace(",", "")) if row.get("award_amount") else 0
        except (ValueError, TypeError):
            amt = 0
        winner_amounts[biz_no] = winner_amounts.get(biz_no, 0) + amt
        winner_names[biz_no] = row.get("winner_name") or winner_names.get(biz_no, "")

    top_winners = [
        {
            "vendor_biz_no": bn,
            "vendor_name": winner_names.get(bn),
            "award_count": cnt,
            "award_total_won": winner_amounts.get(bn, 0),
        }
        for bn, cnt in winner_counter.most_common(10)
    ]

    return {
        "starting_key": "inst_code",
        "keys": {
            "inst_code": inst_code,
            "inst_name": inst_name,
        },
        "sections": {
            "notices": notices,
            "awards": awards,
        },
        "summary": {
            "notice_count": len(notices.get("items", [])),
            "award_count": len(award_items),
            "unique_winners": len(winner_counter),
            "top_winners": top_winners,
            "biz_type": biz_type,
            "date_range": [date_from, date_to],
        },
    }


# === 3. lookup_by_biz_no ===

async def lookup_by_biz_no(
    vendor_biz_no: str,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 30,
) -> dict:
    """사업자번호로 시작하여 NTS 진위 + 낙찰 공고번호 목록 + 거래 발주기관 분포 추적."""
    sections: dict[str, Any] = {}

    # NTS 진위
    try:
        nts = await vendor_tools.check_business_status([vendor_biz_no])
        sections["nts_status"] = nts
    except Exception as exc:  # noqa: BLE001
        sections["nts_status"] = {"error": str(exc)[:200]}

    # 낙찰 이력
    awards = await award_tools.search_awards_by_vendor(
        vendor_biz_no=vendor_biz_no,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    sections["awards"] = awards

    # 발주기관 분포
    inst_counter: Counter[str] = Counter()
    inst_amounts: dict[str, int] = {}
    bid_no_list: list[str] = []
    for row in awards.get("items", []):
        bn = row.get("bid_notice_no")
        if bn:
            bid_no_list.append(bn)
        inst = row.get("inst_name")
        if inst:
            inst_counter[inst] += 1
            try:
                amt = int(str(row.get("award_amount", 0)).replace(",", "")) if row.get("award_amount") else 0
            except (ValueError, TypeError):
                amt = 0
            inst_amounts[inst] = inst_amounts.get(inst, 0) + amt

    top_insts = [
        {
            "inst_name": inst,
            "deal_count": cnt,
            "deal_total_won": inst_amounts.get(inst, 0),
        }
        for inst, cnt in inst_counter.most_common(10)
    ]

    nts_status_code = (
        _safe_get(sections, "nts_status", "items", 0, "b_stt_cd")
        or _safe_get(sections, "nts_status", "items", 0, "b_stt")
    )

    return {
        "starting_key": "vendor_biz_no",
        "keys": {"vendor_biz_no": vendor_biz_no},
        "sections": sections,
        "summary": {
            "nts_status_code": nts_status_code,
            "award_count": len(awards.get("items", [])),
            "bid_notice_no_list": bid_no_list[:20],
            "top_agencies": top_insts,
            "date_range": [date_from, date_to],
        },
    }


# === 4. lookup_by_contract_no (스텁) ===

async def lookup_by_contract_no(contract_no: str) -> dict:
    """계약번호로 시작하여 공고번호·낙찰자·발주기관 추적 (스텁).

    별개 서비스 "계약정보서비스(15129427)" 키 필요.
    현재 G2B_KEY_CONTRACT는 계약과정통합공개용이라 계약번호 단독 조회 불가.
    """
    return {
        "starting_key": "contract_no",
        "keys": {"contract_no": contract_no},
        "status": "not_implemented",
        "note": "계약정보서비스(15129427) 키 신청 후 구현 예정. 현재 G2B_KEY_CONTRACT는 계약과정통합공개용.",
    }
