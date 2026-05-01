"""학습 데이터 수집 — search_awards 누적 결과를 ML 학습용 dataset으로 변환.

사용자 5/2 24번 [NEXT-5]. prediction.py의 휴리스틱 모델을
LightGBM 회귀 모델로 업그레이드하기 위한 학습 데이터 파이프라인.

피처(features):
- biz_type_code: 1(공사) / 2(용역) / 3(물품)
- inst_code_hash: 발주기관 해시 (categorical → numeric)
- estimated_price_log: log10(추정가)
- year, month, day_of_week
- region_code: 지역 코드
- (선택) keyword_embedding: BGE-M3 1024dim

타깃(target):
- award_rate: 낙찰률 (회귀)

산출물:
- runtime/ml/dataset_YYYYMMDD.parquet (또는 csv)
"""
from __future__ import annotations
import asyncio
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.tools import award as award_tools


DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "runtime" / "ml"
DATASET_DIR.mkdir(parents=True, exist_ok=True)


def _to_int(v: Any) -> int:
    if v is None:
        return 0
    try:
        return int(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def _to_rate(v: Any) -> float | None:
    if v is None:
        return None
    try:
        r = float(str(v).replace("%", "").strip())
        if r > 1 and r < 200:
            r = r / 100.0
        return r if 0 < r < 2 else None
    except (ValueError, TypeError):
        return None


def _hash_categorical(s: str | None, modulo: int = 1000) -> int:
    if not s:
        return 0
    h = hashlib.md5(s.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % modulo


def row_to_features(row: dict) -> dict | None:
    """1개 낙찰 row → ML 피처 dict. 결측 시 None."""
    rate = _to_rate(row.get("award_rate"))
    if rate is None:
        return None

    biz_type_map = {"공사": 1, "용역": 2, "물품": 3, "외자": 4}
    biz_type_code = biz_type_map.get(row.get("biz_type") or "", 0)

    open_date = (row.get("open_date") or "")[:8]
    try:
        dt = datetime.strptime(open_date, "%Y%m%d")
        year, month, dow = dt.year, dt.month, dt.weekday()
    except ValueError:
        year, month, dow = 0, 0, 0

    award_amount = _to_int(row.get("award_amount"))
    if award_amount <= 0:
        return None

    import math
    price_log = math.log10(max(award_amount, 1))

    return {
        # features
        "biz_type_code": biz_type_code,
        "inst_code_hash": _hash_categorical(row.get("inst_name")),
        "winner_biz_no_hash": _hash_categorical(row.get("winner_biz_no")),
        "price_log": round(price_log, 4),
        "year": year,
        "month": month,
        "dow": dow,
        # target
        "award_rate": round(rate, 6),
        # raw (학습 후 분석용)
        "_bid_notice_no": row.get("bid_notice_no"),
        "_inst_name": row.get("inst_name"),
        "_award_amount": award_amount,
    }


async def collect_dataset(
    days: int = 90,
    biz_type: str | None = None,
    out_path: Path | None = None,
) -> dict:
    """N일치 낙찰 데이터 수집 → CSV 저장.

    Args:
        days: 최근 N일
        biz_type: 업종 필터 (None=전체)
        out_path: 출력 경로 (기본 runtime/ml/dataset_YYYYMMDD.csv)
    """
    end = datetime.now()
    start = end - timedelta(days=days)
    date_from = start.strftime("%Y%m%d")
    date_to = end.strftime("%Y%m%d")

    print(f"[1/2] 낙찰 데이터 수집: {date_from} ~ {date_to} (biz_type={biz_type or 'all'})")

    awards = await award_tools.search_awards(
        date_from=date_from,
        date_to=date_to,
        biz_type=biz_type,
        limit=1000,
    )
    items = awards.get("items", [])
    print(f"  → {len(items)}건 수집")

    print("[2/2] 피처 변환")
    rows = []
    for it in items:
        f = row_to_features(it)
        if f:
            rows.append(f)
    print(f"  → 유효 학습 데이터: {len(rows)}건 (결측 제외)")

    # CSV 저장 (pandas 의존성 회피, 표준 csv 사용)
    if not out_path:
        out_path = DATASET_DIR / f"dataset_{end.strftime('%Y%m%d')}.csv"

    if rows:
        import csv
        keys = list(rows[0].keys())
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        print(f"  → 저장: {out_path}")

    return {
        "out_path": str(out_path),
        "row_count": len(rows),
        "raw_count": len(items),
        "date_range": [date_from, date_to],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--biz-type", type=str, default=None)
    args = parser.parse_args()

    result = asyncio.run(collect_dataset(args.days, args.biz_type))
    print(f"\n완료: {result}")
