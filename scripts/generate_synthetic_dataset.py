"""합성 학습 데이터셋 생성 — 실 G2B 키 없이 ML 파이프라인 자체 검증.

train_v2.py 의 시계열 split + GridSearch + SHAP 통합을 입증하기 위한 fixture.
실제 학습용은 아니며, runtime/ml/dataset_synth_YYYYMMDD.csv 로 별도 저장.

사용:
    python scripts/generate_synthetic_dataset.py --rows 500
    python -m app.ml.train_v2  # synth 데이터로 학습 통합 검증
"""
from __future__ import annotations
import argparse
import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent.parent / "runtime" / "ml"
DATASET_DIR.mkdir(parents=True, exist_ok=True)


def generate_synthetic_row(rng: random.Random, day_offset: int) -> dict:
    """1개 행 — 실 G2B 패턴(낙찰률 70~95%)을 모사."""
    biz_type_code = rng.choice([1, 2, 3])  # 공사/용역/물품
    inst_code_hash = rng.randint(0, 999)
    winner_biz_no_hash = rng.randint(0, 999)
    region_code = rng.choices(
        list(range(0, 18)),
        weights=[5, 30, 8, 8, 8, 5, 5, 4, 3, 15, 3, 3, 3, 2, 2, 3, 3, 1],
        k=1,
    )[0]

    # 추정가 분포 — log-normal
    amount = int(10 ** rng.uniform(7.0, 10.5))
    if amount < 1e8:
        amount_bucket = 1
    elif amount < 1e9:
        amount_bucket = 2
    elif amount < 1e10:
        amount_bucket = 3
    else:
        amount_bucket = 4
    price_log = round(math.log10(max(amount, 1)), 4)

    # 날짜
    base_dt = datetime(2025, 1, 1) + timedelta(days=day_offset)
    year, month, dow = base_dt.year, base_dt.month, base_dt.weekday()
    quarter = (month - 1) // 3 + 1
    is_year_end = 1 if month == 12 else 0

    # 낙찰률 — 업종/지역/금액에 따른 약한 의존성 + 노이즈
    base_rate = 0.85
    base_rate += (biz_type_code - 2) * 0.01  # 공사 1 < 용역 2 < 물품 3
    base_rate -= amount_bucket * 0.005  # 큰 금액일수록 낮은 낙찰률
    base_rate += (region_code - 9) * 0.0005  # 지역별 미세 차이
    base_rate += rng.gauss(0, 0.04)  # 노이즈
    award_rate = max(0.6, min(1.05, base_rate))

    return {
        "biz_type_code": biz_type_code,
        "inst_code_hash": inst_code_hash,
        "winner_biz_no_hash": winner_biz_no_hash,
        "region_code": region_code,
        "amount_bucket": amount_bucket,
        "price_log": price_log,
        "year": year,
        "month": month,
        "dow": dow,
        "quarter": quarter,
        "is_year_end": is_year_end,
        "award_rate": round(award_rate, 6),
        "_bid_notice_no": f"SYNTH{day_offset:06d}",
        "_inst_name": "synthetic",
        "_award_amount": amount,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=500)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    rng = random.Random(args.seed)
    rows = [generate_synthetic_row(rng, i // 3) for i in range(args.rows)]

    out = DATASET_DIR / f"dataset_synth_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"synthetic dataset: {len(rows)} rows -> {out}")
    print(
        f"  award_rate distribution: "
        f"min={min(r['award_rate'] for r in rows):.3f} "
        f"max={max(r['award_rate'] for r in rows):.3f} "
        f"mean={sum(r['award_rate'] for r in rows) / len(rows):.3f}"
    )


if __name__ == "__main__":
    main()
