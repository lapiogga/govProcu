"""ML 모델 캘리브레이션 — predict ↔ histogram 비교 + 신뢰도 평가.

NEXT2-2: 모델 예측이 실제 분포와 얼마나 일치하는지 검증.

기능:
1. 학습된 모델 예측값 vs 실제 낙찰률 산점 (residual analysis)
2. 분위수별 calibration curve (예측 p10/p50/p90 → 실제 p10/p50/p90 매칭)
3. Mean Absolute Calibration Error (MACE)
4. Bin-wise reliability diagram

산출:
    runtime/ml/calibration_report.json
"""
from __future__ import annotations
import json
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "runtime" / "ml"


def calibrate(csv_path: Path | None = None) -> dict:
    """학습/테스트 분리 + 예측 vs 실제 분포 비교."""
    try:
        import lightgbm as lgb
        import pandas as pd
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, mean_squared_error
    except ImportError:
        return {"error": "pip install lightgbm scikit-learn pandas numpy"}

    from app.ml.train import FEATURES, TARGET

    if csv_path is None:
        csvs = sorted(DATASET_DIR.glob("dataset_*.csv"))
        if not csvs:
            return {"error": "no dataset"}
        csv_path = csvs[-1]

    df = pd.read_csv(csv_path)
    if len(df) < 30:
        return {"error": "insufficient data", "rows": len(df)}

    X = df[FEATURES].values
    y = df[TARGET].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model_path = DATASET_DIR / "model_award_rate.txt"
    if not model_path.exists():
        return {"error": "model not trained yet. run app.ml.train first"}
    booster = lgb.Booster(model_file=str(model_path))
    y_pred = booster.predict(X_test)

    # 1. 기본 메트릭
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

    # 2. 분위수별 calibration
    quantiles = [0.1, 0.25, 0.5, 0.75, 0.9]
    pred_q = {f"p{int(q*100)}": float(np.quantile(y_pred, q)) for q in quantiles}
    actual_q = {f"p{int(q*100)}": float(np.quantile(y_test, q)) for q in quantiles}

    quantile_diffs = {
        q: pred_q[q] - actual_q[q] for q in pred_q
    }

    # 3. Bin-wise reliability (예측 0.7~1.0 사이 10개 bin)
    bins = np.linspace(0.7, 1.0, 11)
    bin_data = []
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        mask = (y_pred >= lo) & (y_pred < hi)
        n = int(mask.sum())
        if n == 0:
            continue
        bin_data.append({
            "bin_low": float(lo),
            "bin_high": float(hi),
            "count": n,
            "pred_mean": float(y_pred[mask].mean()),
            "actual_mean": float(y_test[mask].mean()),
            "abs_error": float(abs(y_pred[mask].mean() - y_test[mask].mean())),
        })

    # 4. Mean Absolute Calibration Error
    if bin_data:
        mace = sum(b["abs_error"] * b["count"] for b in bin_data) / sum(
            b["count"] for b in bin_data
        )
    else:
        mace = None

    report = {
        "dataset": str(csv_path),
        "test_size": int(len(y_test)),
        "metrics": {
            "mae_pct": round(mae * 100, 4),
            "rmse_pct": round(rmse * 100, 4),
            "mace_pct": round(mace * 100, 4) if mace else None,
        },
        "quantile_calibration": {
            "predicted": pred_q,
            "actual": actual_q,
            "diff": quantile_diffs,
        },
        "reliability_bins": bin_data,
        "interpretation": _interpret(mae, mace),
    }

    out_path = DATASET_DIR / "calibration_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {out_path}")
    return report


def _interpret(mae: float, mace: float | None) -> str:
    if mae < 0.02:
        m = "MAE 매우 우수 (2%p 미만)"
    elif mae < 0.05:
        m = "MAE 양호 (5%p 미만)"
    else:
        m = "MAE 부족 — 데이터·feature 보강 필요"

    if mace is None:
        c = ""
    elif mace < 0.02:
        c = " · calibration 양호"
    elif mace < 0.05:
        c = " · calibration 보통"
    else:
        c = " · calibration 보정 필요"
    return m + c


if __name__ == "__main__":
    result = calibrate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
