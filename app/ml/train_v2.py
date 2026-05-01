"""ML 학습 v2 — 시계열 split + GridSearchCV + SHAP feature importance.

NEXT6-3: train.py v1 보다 정밀화.
- TimeSeriesSplit (k=5)
- GridSearchCV (n_estimators, max_depth, learning_rate, num_leaves)
- SHAP TreeExplainer → 평균 절댓값 기반 importance
- 검증 결과 + 캘리브레이션 통합 보고

산출:
    runtime/ml/model_award_rate_v2.txt
    runtime/ml/model_meta_v2.json
    runtime/ml/shap_summary.json
"""
from __future__ import annotations
import json
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "runtime" / "ml"


def train_v2(csv_path: Path | None = None) -> dict:
    """시계열 split + GridSearch + SHAP 통합 학습."""
    try:
        import lightgbm as lgb
        import numpy as np
        import pandas as pd
        from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
        from sklearn.metrics import mean_absolute_error, r2_score
    except ImportError:
        return {"error": "pip install lightgbm scikit-learn pandas numpy"}

    from app.ml.train import FEATURES, TARGET

    if csv_path is None:
        csvs = sorted(DATASET_DIR.glob("dataset_*.csv"))
        if not csvs:
            return {"error": "no dataset"}
        csv_path = csvs[-1]

    df = pd.read_csv(csv_path)
    if len(df) < 50:
        return {"error": "insufficient data", "rows": len(df)}

    # 시계열 정렬 (year * 100 + month 가상 순서)
    if "year" in df.columns and "month" in df.columns:
        df["_ts"] = df["year"] * 100 + df["month"]
        df = df.sort_values("_ts").drop(columns=["_ts"])

    X = df[FEATURES].values
    y = df[TARGET].values

    # 시계열 5-fold (시간 순서 유지)
    tscv = TimeSeriesSplit(n_splits=5)

    # GridSearch 파라미터 (작은 격자 — 빠른 검증)
    param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [4, 6, 8],
        "learning_rate": [0.05, 0.1],
        "num_leaves": [15, 31],
    }

    base = lgb.LGBMRegressor(
        objective="regression",
        min_child_samples=5,
        verbosity=-1,
        random_state=42,
    )

    print(f"GridSearchCV: {len(X)} rows, 5-fold time-series, "
          f"{2*3*2*2}=24 candidates")

    grid = GridSearchCV(
        base,
        param_grid,
        cv=tscv,
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
    )
    grid.fit(X, y)
    best = grid.best_estimator_

    # holdout = 마지막 20%
    n = len(X)
    cut = int(n * 0.8)
    X_train, X_test = X[:cut], X[cut:]
    y_train, y_test = y[:cut], y[cut:]
    best.fit(X_train, y_train)
    y_pred = best.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    # SHAP feature importance
    shap_summary = _compute_shap(best, X_train[:200], FEATURES)

    # 저장
    model_path = DATASET_DIR / "model_award_rate_v2.txt"
    meta_path = DATASET_DIR / "model_meta_v2.json"
    shap_path = DATASET_DIR / "shap_summary.json"
    best.booster_.save_model(str(model_path))

    meta = {
        "model_type": "LightGBM Regressor v2 (TimeSeriesSplit + GridSearch)",
        "best_params": grid.best_params_,
        "cv_best_score": -float(grid.best_score_),
        "test_mae_pct": round(mae * 100, 4),
        "test_r2": round(r2, 4),
        "test_size": int(len(X_test)),
        "train_size": int(len(X_train)),
        "features": FEATURES,
        "feature_importance_gain": dict(zip(FEATURES, best.feature_importances_.tolist())),
        "dataset_path": str(csv_path),
        "shap_summary_path": str(shap_path),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    shap_path.write_text(json.dumps(shap_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nMAE {mae*100:.3f}%p · R² {r2:.4f}")
    print(f"Best params: {grid.best_params_}")
    print(f"Saved: {model_path}, {meta_path}, {shap_path}")
    return meta


def _compute_shap(model, X_sample, features) -> dict:
    """SHAP TreeExplainer — feature 평균 절댓값 importance."""
    try:
        import shap  # type: ignore[import-untyped]
        import numpy as np
    except ImportError:
        return {"error": "pip install shap"}

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    if hasattr(shap_values, "shape") and len(shap_values.shape) == 2:
        mean_abs = np.abs(shap_values).mean(axis=0)
    else:
        mean_abs = np.abs(np.array(shap_values)).mean(axis=0)

    return {
        "method": "shap.TreeExplainer mean abs",
        "sample_size": int(len(X_sample)),
        "importance": [
            {"feature": f, "mean_abs_shap": float(v)}
            for f, v in sorted(
                zip(features, mean_abs), key=lambda kv: -kv[1]
            )
        ],
    }


if __name__ == "__main__":
    result = train_v2()
    print(json.dumps(result, ensure_ascii=False, indent=2))
