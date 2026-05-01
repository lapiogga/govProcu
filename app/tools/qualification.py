"""qualification 영역 MCP 도구 — 적격심사 점수계산기.

사용자 5/2 22번 우선순위 P0 (필수, 시장 진입 자격).
경쟁사(인포21C·비드프로·비드큐·아이건설넷) 핵심 기능. 건설·전문건설 시장 1순위 활용.

도구:
- calc_qualification_score: 적격심사 점수 종합 계산
- calc_bid_price_score: 입찰가격 점수 단독 계산 (낙찰하한율 기반)
- get_qualification_rule: 입찰 유형별 적격심사 산식 안내

산식 근거:
- 「국가계약법 시행령」 제42조 + 조달청 적격심사 세부기준
- 공사·용역·물품, 추정가격대(추정가격 1억 미만/100억 미만/100억 이상 등)별 가중치 차등
- 본 모듈은 일반적 골격이며, 발주기관·공사 종류별 세부 가중치는 사용자가 override 가능

운영 단계에서 발주기관별 실제 산식(공고문 PDF에서 OCR로 추출) 통합 가능.
"""
from __future__ import annotations
from typing import Literal


BizType = Literal["공사", "용역", "물품"]


# === 표준 가중치 (조달청 적격심사 일반) ===
# 공사 추정가격 100억 미만 (가장 흔한 케이스)
_DEFAULT_WEIGHTS_CNSTWK_LT100 = {
    "bid_price": 30.0,        # 입찰가격
    "experience": 13.0,       # 시공경험 (실적)
    "tech_capability": 12.0,  # 기술능력 (기술자 보유)
    "management": 15.0,       # 경영상태 (신용평가)
    "credit": 15.0,           # 신인도
    "etc": 15.0,              # 기타 (지역가산 등)
}

# 공사 추정가격 100억 이상
_DEFAULT_WEIGHTS_CNSTWK_GT100 = {
    "bid_price": 30.0,
    "experience": 18.0,
    "tech_capability": 13.0,
    "management": 14.0,
    "credit": 13.0,
    "etc": 12.0,
}

# 용역 (일반)
_DEFAULT_WEIGHTS_SERVC = {
    "bid_price": 30.0,
    "experience": 25.0,
    "tech_capability": 20.0,
    "management": 10.0,
    "credit": 10.0,
    "etc": 5.0,
}

# 물품
_DEFAULT_WEIGHTS_THNG = {
    "bid_price": 35.0,
    "experience": 20.0,
    "tech_capability": 15.0,
    "management": 15.0,
    "credit": 10.0,
    "etc": 5.0,
}


def get_default_weights(biz_type: BizType, estimated_price: int | None = None) -> dict:
    """입찰 유형·금액대별 기본 가중치 반환."""
    if biz_type == "공사":
        if estimated_price and estimated_price >= 10_000_000_000:  # 100억 이상
            return dict(_DEFAULT_WEIGHTS_CNSTWK_GT100)
        return dict(_DEFAULT_WEIGHTS_CNSTWK_LT100)
    if biz_type == "용역":
        return dict(_DEFAULT_WEIGHTS_SERVC)
    if biz_type == "물품":
        return dict(_DEFAULT_WEIGHTS_THNG)
    return dict(_DEFAULT_WEIGHTS_CNSTWK_LT100)


# === 산식 함수 ===

def _bid_price_score(
    bid_amount: int,
    base_amount: int,
    biz_type: BizType,
    estimated_price: int | None = None,
    max_score: float = 30.0,
) -> tuple[float, dict]:
    """입찰가격 점수 — 낙찰하한율 대비 입찰가 비율로 계산.

    조달청 표준: 낙찰하한율(공사 87.745%, 용역 80~88%, 물품 88%) 이상이면서
    예정가격 이하 범위에서 가장 낮은 입찰가에 가까울수록 만점.

    Args:
        bid_amount: 응찰가 (원)
        base_amount: 기초금액 또는 예정가격 (원)
        biz_type: 입찰 유형
        estimated_price: 추정가격 (가산점 산정용)
        max_score: 최대 점수 (기본 30점)

    Returns:
        (점수, 상세 정보)
    """
    # 입찰 유형별 낙찰하한율 (조달청 일반)
    if biz_type == "공사":
        lower_rate = 0.87745  # 87.745%
    elif biz_type == "용역":
        lower_rate = 0.80  # 80% (일반용역 기본)
    else:  # 물품
        lower_rate = 0.88

    bid_rate = bid_amount / base_amount if base_amount else 0.0
    lower_amount = int(base_amount * lower_rate)

    if bid_rate < lower_rate:
        # 낙찰하한 미달 — 0점
        return 0.0, {
            "bid_rate_pct": round(bid_rate * 100, 3),
            "lower_rate_pct": round(lower_rate * 100, 3),
            "status": "낙찰하한 미달",
            "lower_amount": lower_amount,
        }

    if bid_amount > base_amount:
        # 예정가 초과 — 0점
        return 0.0, {
            "bid_rate_pct": round(bid_rate * 100, 3),
            "status": "예정가격 초과",
        }

    # 점수: 낙찰하한율~100% 구간에서 비례 (낮을수록 점수↑은 일반론, 적격심사는 보통 높을수록 만점)
    # 단순 모델: bid_rate가 낙찰하한율에 가까울수록 만점, 100%에 가까울수록 감점
    # max_score * (1 - (bid_rate - lower_rate) / (1.0 - lower_rate)) — 하한이 만점
    span = 1.0 - lower_rate
    proximity = (bid_rate - lower_rate) / span if span > 0 else 0
    score = max_score * (1.0 - proximity)

    return round(score, 3), {
        "bid_rate_pct": round(bid_rate * 100, 3),
        "lower_rate_pct": round(lower_rate * 100, 3),
        "status": "정상 범위",
        "lower_amount": lower_amount,
    }


def _experience_score(
    actual: float,
    standard: float,
    max_score: float = 13.0,
) -> tuple[float, dict]:
    """시공경험 점수 — 실적/기준."""
    if standard <= 0:
        return 0.0, {"actual": actual, "standard": standard, "status": "기준 0"}
    ratio = actual / standard
    score = min(max_score, max_score * ratio)
    return round(score, 3), {
        "actual": actual,
        "standard": standard,
        "ratio_pct": round(ratio * 100, 2),
    }


def _tech_score(
    tech_count: int,
    required_count: int,
    max_score: float = 12.0,
) -> tuple[float, dict]:
    """기술능력 점수 — 기술자 보유."""
    if required_count <= 0:
        return max_score, {"tech_count": tech_count, "required": required_count}
    ratio = tech_count / required_count
    score = min(max_score, max_score * ratio)
    return round(score, 3), {
        "tech_count": tech_count,
        "required": required_count,
        "ratio_pct": round(ratio * 100, 2),
    }


def _credit_score(credit_grade: str | None, max_score: float = 15.0) -> tuple[float, dict]:
    """신용평가 점수 — 등급별."""
    grade_map = {
        "AAA": 1.00, "AA+": 0.98, "AA": 0.95, "AA-": 0.93,
        "A+": 0.90, "A": 0.87, "A-": 0.85,
        "BBB+": 0.80, "BBB": 0.75, "BBB-": 0.70,
        "BB+": 0.60, "BB": 0.50, "BB-": 0.40,
        "B": 0.30, "CCC": 0.20, "C": 0.10, "D": 0.0,
    }
    if not credit_grade:
        return max_score * 0.7, {"grade": None, "ratio": 0.7, "note": "등급 미입력 — 평균 70%"}
    ratio = grade_map.get(credit_grade.upper().strip(), 0.7)
    score = max_score * ratio
    return round(score, 3), {"grade": credit_grade, "ratio": ratio}


# === 메인 도구 ===

async def calc_qualification_score(
    bid_amount: int,
    base_amount: int,
    biz_type: BizType,
    estimated_price: int | None = None,
    experience_actual: float = 0.0,
    experience_standard: float = 1.0,
    tech_count: int = 0,
    tech_required: int = 1,
    credit_grade: str | None = None,
    management_score_pct: float = 80.0,
    etc_score_pct: float = 80.0,
    weights_override: dict | None = None,
) -> dict:
    """적격심사 점수 종합 계산.

    Args:
        bid_amount: 응찰가 (원)
        base_amount: 기초금액 또는 예정가격 (원)
        biz_type: '공사'/'용역'/'물품'
        estimated_price: 추정가격 (옵션, 100억 기준 가중치 분기)
        experience_actual: 시공경험 실적 (예: 최근 5년 누적 공사금액 원)
        experience_standard: 시공경험 기준 (예: 추정가격의 N배)
        tech_count: 보유 기술자 수
        tech_required: 요구 기술자 수
        credit_grade: 신용평가 등급 (예: 'AA-', 'BBB+')
        management_score_pct: 경영상태 점수 비율 (0~100, 기본 80%)
        etc_score_pct: 기타 점수 비율 (0~100, 기본 80%)
        weights_override: 가중치 override (발주기관별 차등 시)

    Returns:
        총점 + 항목별 점수 상세 dict.
    """
    weights = weights_override or get_default_weights(biz_type, estimated_price)

    bid_score, bid_detail = _bid_price_score(
        bid_amount, base_amount, biz_type, estimated_price, weights["bid_price"]
    )
    exp_score, exp_detail = _experience_score(
        experience_actual, experience_standard, weights["experience"]
    )
    tech_score_v, tech_detail = _tech_score(tech_count, tech_required, weights["tech_capability"])
    cred_score, cred_detail = _credit_score(credit_grade, weights["credit"])

    mgmt_score = round(weights["management"] * (management_score_pct / 100.0), 3)
    etc_score = round(weights["etc"] * (etc_score_pct / 100.0), 3)

    total = bid_score + exp_score + tech_score_v + cred_score + mgmt_score + etc_score
    max_total = sum(weights.values())

    return {
        "biz_type": biz_type,
        "estimated_price": estimated_price,
        "weights": weights,
        "scores": {
            "bid_price": {"score": bid_score, "max": weights["bid_price"], "detail": bid_detail},
            "experience": {"score": exp_score, "max": weights["experience"], "detail": exp_detail},
            "tech_capability": {
                "score": tech_score_v, "max": weights["tech_capability"], "detail": tech_detail
            },
            "credit": {"score": cred_score, "max": weights["credit"], "detail": cred_detail},
            "management": {"score": mgmt_score, "max": weights["management"]},
            "etc": {"score": etc_score, "max": weights["etc"]},
        },
        "total": round(total, 3),
        "max_total": max_total,
        "ratio_pct": round(total / max_total * 100, 2) if max_total else 0,
        "note": "조달청 적격심사 일반 모델 — 발주기관별 세부기준 차등 시 weights_override 사용.",
    }


async def calc_bid_price_score(
    bid_amount: int,
    base_amount: int,
    biz_type: BizType,
    max_score: float = 30.0,
) -> dict:
    """입찰가격 점수 단독 계산 (낙찰하한율 기반)."""
    score, detail = _bid_price_score(bid_amount, base_amount, biz_type, max_score=max_score)
    return {
        "biz_type": biz_type,
        "bid_amount": bid_amount,
        "base_amount": base_amount,
        "max_score": max_score,
        "score": score,
        "detail": detail,
    }


async def get_qualification_rule(
    biz_type: BizType,
    estimated_price: int | None = None,
) -> dict:
    """입찰 유형·금액대별 적격심사 산식 가중치 안내."""
    weights = get_default_weights(biz_type, estimated_price)
    return {
        "biz_type": biz_type,
        "estimated_price": estimated_price,
        "weights": weights,
        "max_total": sum(weights.values()),
        "lower_rate_default": {
            "공사": "87.745%",
            "용역": "80% (일반)",
            "물품": "88%",
        }[biz_type],
        "note": "조달청 표준 산식. 발주기관·공사 유형별 세부기준은 공고문 참조.",
    }
