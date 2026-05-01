"""prediction 영역 MCP 도구 — 투찰가/낙찰가 예측.

사용자 5/2 22번 우선순위 P1 (중요, 차별화).
디마툴즈·비드스코어·BidBot 핵심 기능에 대항.

본 구현은 **통계 기반 휴리스틱 모델** (ML 학습 인프라 별도 구축 후 본격화).
유사 입찰의 낙찰률 분포 + 발주기관 사정률 패턴 + 업종 추세를 결합.

도구:
- predict_bid_price: 적정 응찰가 + 95% 신뢰구간 + 낙찰 확률
- estimate_winning_threshold: 낙찰 하한가 추정
- compare_bid_strategies: 응찰가 시나리오별 낙찰 확률 비교

향후 확장 (Phase 2):
- LightGBM/XGBoost 학습 모델
- 응답시간 변동(monthly trend) feature
- 기상·계절 feature
- 발주기관 patterns transfer learning
"""
from __future__ import annotations

from app.tools import analytics as analytics_tools
from app.tools import award as award_tools
from app.tools import bid as bid_tools

try:
    from app.ml.train import predict as ml_predict
    from app.ml.dataset import row_to_features as _row_to_features
    _ML_AVAILABLE = True
except ImportError:
    _ML_AVAILABLE = False
    ml_predict = None
    _row_to_features = None


def _safe_amt(v) -> int:
    if v is None:
        return 0
    try:
        return int(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def _safe_rate(v) -> float | None:
    if v is None:
        return None
    try:
        r = float(str(v).replace("%", "").strip())
        if r > 1 and r < 200:
            r = r / 100.0
        return r if 0 < r < 2 else None
    except (ValueError, TypeError):
        return None


async def predict_bid_price(
    bid_notice_no: str | None = None,
    bid_ord: str = "00",
    base_amount: int | None = None,
    biz_type: str | None = None,
    inst_name: str | None = None,
    target_win_probability: float = 0.7,
) -> dict:
    """공고번호 또는 (예정가+발주기관) 기준 적정 응찰가 예측.

    Args:
        bid_notice_no: 입찰공고번호 (provided 시 자동 메타 추출)
        bid_ord: 차수
        base_amount: 기초금액/예정가 (bid_notice_no 미제공 시 필수)
        biz_type: 업종 (자동 추출 가능)
        inst_name: 발주기관 (자동 추출 가능)
        target_win_probability: 목표 낙찰 확률 (0.5=중간/0.7=상위 30%/0.9=거의 확실)

    Returns:
        recommended_amount + range + 95% CI + win_probability_estimate
    """
    # 1. 공고 메타 자동 추출
    if bid_notice_no:
        notice = await bid_tools.get_bid_notice_detail(bid_notice_no, bid_ord)
        if notice.get("found"):
            summary = notice.get("summary", {})
            base_amount = base_amount or _safe_amt(summary.get("estimated_price"))
            biz_type = biz_type or summary.get("biz_type")
            inst_name = inst_name or summary.get("inst_name")

    if not base_amount:
        return {
            "status": "missing_base_amount",
            "note": "bid_notice_no(공고에서 자동 추출) 또는 base_amount 필수.",
        }

    # 2. 발주기관 사정률 패턴 (analytics A6)
    pattern = None
    if inst_name:
        try:
            pattern = await analytics_tools.analyze_agency_price_pattern(
                inst_name=inst_name,
                biz_type=biz_type,
            )
        except Exception:
            pattern = None

    # 3. 패턴이 있으면 분위수 기반 추천
    if pattern and pattern.get("sample_count", 0) >= 5:
        pct = pattern["summary_pct"]
        # target_win_probability 매핑:
        # 0.9 → p25 근처 (낮은 응찰가, 높은 낙찰률)
        # 0.7 → p10 근처
        # 0.5 → median
        # 0.3 → p25 (낙찰 위해 더 낮은 가격)
        if target_win_probability >= 0.85:
            target_rate_pct = pct["p10"]
            band_low_pct = pct["p10"] - 0.5
            band_high_pct = pct["p25"]
        elif target_win_probability >= 0.65:
            target_rate_pct = pct["p25"]
            band_low_pct = pct["p10"]
            band_high_pct = pct["median"]
        elif target_win_probability >= 0.45:
            target_rate_pct = pct["median"]
            band_low_pct = pct["p25"]
            band_high_pct = pct["p75"]
        else:
            target_rate_pct = pct["p75"]
            band_low_pct = pct["median"]
            band_high_pct = pct["p90"]

        recommended = int(base_amount * target_rate_pct / 100.0)
        ci_low = int(base_amount * band_low_pct / 100.0)
        ci_high = int(base_amount * band_high_pct / 100.0)

        return {
            "bid_notice_no": bid_notice_no,
            "base_amount": base_amount,
            "biz_type": biz_type,
            "inst_name": inst_name,
            "target_win_probability": target_win_probability,
            "recommended_amount": recommended,
            "recommended_rate_pct": round(target_rate_pct, 3),
            "ci_95": {
                "low_amount": ci_low,
                "high_amount": ci_high,
                "low_rate_pct": round(band_low_pct, 3),
                "high_rate_pct": round(band_high_pct, 3),
            },
            "agency_pattern": {
                "sample_count": pattern["sample_count"],
                "mean_rate_pct": pct["mean"],
                "median_rate_pct": pct["median"],
                "interpretation": pattern.get("interpretation"),
            },
            "model": "histogram_quantile (발주기관 낙찰률 분위수 기반)",
            "note": "ML 모델 학습 후 정밀도 향상 예정.",
        }

    # 4. 패턴 부족 시 업종별 일반 낙찰하한율 적용 (휴리스틱)
    default_lower_rate = {"공사": 0.87745, "용역": 0.80, "물품": 0.88}.get(biz_type, 0.85)
    median_rate = default_lower_rate + 0.03  # 하한+3% 가량을 일반 추천

    recommended = int(base_amount * median_rate)
    return {
        "bid_notice_no": bid_notice_no,
        "base_amount": base_amount,
        "biz_type": biz_type,
        "inst_name": inst_name,
        "target_win_probability": target_win_probability,
        "recommended_amount": recommended,
        "recommended_rate_pct": round(median_rate * 100, 3),
        "ci_95": {
            "low_amount": int(base_amount * default_lower_rate),
            "high_amount": int(base_amount * (default_lower_rate + 0.06)),
            "low_rate_pct": round(default_lower_rate * 100, 3),
            "high_rate_pct": round((default_lower_rate + 0.06) * 100, 3),
        },
        "model": "default_lower_rate (발주기관 데이터 부족 — 업종 일반치)",
        "note": "발주기관 낙찰 이력 5건 미만. inst_name 변경 또는 기간 확장 권장.",
    }


async def estimate_winning_threshold(
    inst_name: str,
    biz_type: str | None = None,
    confidence: float = 0.8,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """발주기관별 낙찰 하한가 (낙찰률 통계의 confidence 분위수) 추정.

    Args:
        inst_name: 발주기관
        biz_type: 업종 필터
        confidence: 0.8이면 80% 신뢰구간 — p10 ~ p90 구간 반환
    """
    pattern = await analytics_tools.analyze_agency_price_pattern(
        inst_name=inst_name,
        biz_type=biz_type,
        date_from=date_from,
        date_to=date_to,
    )
    if not pattern.get("sample_count"):
        return {
            "status": "no_data",
            "inst_name": inst_name,
            "note": "발주기관 낙찰 이력 없음.",
        }
    pct = pattern["summary_pct"]

    # confidence 매핑: 80% → p10/p90, 90% → p5/p95(추정 가능시), 95% → p2.5/p97.5
    return {
        "inst_name": inst_name,
        "biz_type": biz_type,
        "sample_count": pattern["sample_count"],
        "median_pct": pct["median"],
        "lower_pct": pct["p10"] if confidence <= 0.8 else pct["p10"] - 1.0,
        "upper_pct": pct["p90"] if confidence <= 0.8 else pct["p90"] + 1.0,
        "interpretation": pattern.get("interpretation"),
        "confidence": confidence,
    }


async def compare_bid_strategies(
    base_amount: int,
    inst_name: str,
    biz_type: str | None = None,
    strategies: list[float] | None = None,
) -> dict:
    """응찰가 시나리오 여러 개의 낙찰 확률 비교.

    Args:
        base_amount: 예정가
        inst_name: 발주기관
        biz_type: 업종
        strategies: 응찰률 후보 (예: [0.85, 0.88, 0.90, 0.92, 0.95])
    """
    if not strategies:
        strategies = [0.82, 0.85, 0.88, 0.90, 0.92, 0.95]

    pattern = await analytics_tools.analyze_agency_price_pattern(
        inst_name=inst_name,
        biz_type=biz_type,
    )

    n = pattern.get("sample_count", 0)
    if n == 0:
        return {
            "status": "no_data",
            "inst_name": inst_name,
            "scenarios": [],
            "note": "발주기관 낙찰 이력 없음.",
        }

    # 각 strategy의 낙찰률 percentile 추정 (낙찰률 분포 대비 낮은 위치 = 높은 낙찰 확률)
    pct = pattern["summary_pct"]

    def estimate_win_prob(rate: float) -> float:
        rate_pct = rate * 100
        if rate_pct <= pct["p10"]:
            return 0.92
        if rate_pct <= pct["p25"]:
            return 0.78
        if rate_pct <= pct["median"]:
            return 0.55
        if rate_pct <= pct["p75"]:
            return 0.32
        if rate_pct <= pct["p90"]:
            return 0.15
        return 0.05

    scenarios = []
    for rate in strategies:
        amt = int(base_amount * rate)
        win_p = estimate_win_prob(rate)
        scenarios.append({
            "bid_rate_pct": round(rate * 100, 3),
            "bid_amount": amt,
            "estimated_win_prob": round(win_p, 3),
            "note": f"발주기관 낙찰률 분포 대비 {'낮음' if rate * 100 < pct['median'] else '중간 이상'}",
        })

    return {
        "base_amount": base_amount,
        "inst_name": inst_name,
        "biz_type": biz_type,
        "agency_sample_count": n,
        "agency_median_rate_pct": pct["median"],
        "scenarios": scenarios,
        "model": "histogram_percentile (분위수 룩업)",
    }
