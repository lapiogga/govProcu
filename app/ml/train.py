"""LightGBM 학습 스크립트 — 낙찰률 회귀 모델.

사용자 5/2 24번 [NEXT-5]. 첫 baseline 모델.

사용:
    pip install lightgbm scikit-learn pandas
    python -m app.ml.dataset --days 90        # 데이터 수집 먼저
    python -m app.ml.train                     # 학습

산출:
    runtime/ml/model_award_rate.txt (LightGBM 모델)
    runtime/ml/model_meta.json (피처 이름·메트릭)
"""
from __future__ import annotations
import json
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "runtime" / "ml"


FEATURES = [
    "biz_type_code",
    "inst_code_hash",
    "winner_biz_no_hash",
    "price_log",
    "year",
    "month",
    "dow",
]
TARGET = "award_rate"


def load_dataset(csv_path: Path):
    """csv → (X, y) numpy arrays."""
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pip install pandas")
        raise

    df = pd.read_csv(csv_path)
    print(f"loaded {len(df)} rows from {csv_path}")
    X = df[FEATURES].values
    y = df[TARGET].values
    return X, y, df


def train(csv_path: Path | None = None) -> dict:
    """학습 + 평가 + 모델 저장."""
    try:
        import lightgbm as lgb
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, r2_score
    except ImportError:
        print("ERROR: pip install lightgbm scikit-learn pandas")
        return {"error": "missing dependencies"}

    if csv_path is None:
        csvs = sorted(DATASET_DIR.glob("dataset_*.csv"))
        if not csvs:
            return {"error": "no dataset found. run app.ml.dataset first"}
        csv_path = csvs[-1]

    X, y, df = load_dataset(csv_path)
    if len(X) < 30:
        return {
            "error": "insufficient data",
            "row_count": len(X),
            "note": "최소 30건 이상 필요. days 확장 권장.",
        }

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"train={len(X_train)}, test={len(X_test)}")

    model = lgb.LGBMRegressor(
        objective="regression",
        n_estimators=200,
        max_depth=6,
        num_leaves=31,
        learning_rate=0.05,
        min_child_samples=5,
        verbosity=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(20)],
    )

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # 모델 + 메타 저장
    model_path = DATASET_DIR / "model_award_rate.txt"
    meta_path = DATASET_DIR / "model_meta.json"

    model.booster_.save_model(str(model_path))

    feature_importance = dict(zip(FEATURES, model.feature_importances_.tolist()))
    meta = {
        "model_type": "LightGBM Regressor",
        "target": TARGET,
        "features": FEATURES,
        "feature_importance": feature_importance,
        "metrics": {
            "mae": float(mae),
            "r2": float(r2),
            "test_size": len(X_test),
            "train_size": len(X_train),
        },
        "dataset_path": str(csv_path),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n=== 결과 ===")
    print(f"MAE: {mae*100:.3f}%p  R²: {r2:.4f}")
    print(f"Model: {model_path}")
    print(f"Meta: {meta_path}")

    return meta


def predict(features: dict) -> float | None:
    """저장된 모델로 단건 예측. prediction.py에서 호출 가능.

    Args:
        features: {biz_type_code, inst_code_hash, ..., dow}
    Returns:
        predicted award_rate (0~2 범위, None=모델 없음)
    """
    try:
        import lightgbm as lgb
    except ImportError:
        return None

    model_path = DATASET_DIR / "model_award_rate.txt"
    if not model_path.exists():
        return None

    booster = lgb.Booster(model_file=str(model_path))
    X = [[features.get(f, 0) for f in FEATURES]]
    return float(booster.predict(X)[0])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default=None)
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else None
    result = train(csv_path)
    print(f"\n{json.dumps(result, ensure_ascii=False, indent=2)}")
