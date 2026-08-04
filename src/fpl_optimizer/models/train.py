import joblib
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error
from fpl_optimizer.models.dataset import load_training_data

FEATURE_COLS = [
    "now_cost",
    "avg_points_last_3",
    "avg_points_last_5",
    "avg_minutes_last_3",
    "avg_xg_last_3",
    "avg_xa_last_3",
    "std_points_last_5",
    "games_in_window_5",
    "pos_DEF",
    "pos_FWD",
    "pos_GKP",
    "pos_MID",
]

MODEL_PATH = "models/points_predictor_v1.pkl"


def time_based_split(df, val_fraction=0.2):
    """
    Split by gameweek order, not randomly — the last `val_fraction` of
    gameweeks (chronologically) become validation. This mimics how the
    model will actually be used: trained on the past, predicting the future.
    """
    n_val = int(len(df) * val_fraction)
    train_df = df.iloc[:-n_val]
    val_df = df.iloc[-n_val:]
    return train_df, val_df


def train():
    df = load_training_data()

    # Ensure all expected position dummy columns exist even if a position
    # didn't appear in a given slice of data
    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0

    train_df, val_df = time_based_split(df)

    X_train, y_train = train_df[FEATURE_COLS], train_df["target"]
    X_val, y_val = val_df[FEATURE_COLS], val_df["target"]

    model = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        num_leaves=20,
        random_state=42,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="mae",
        callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(period=50)],
    )

    val_preds = model.predict(X_val)
    mae = mean_absolute_error(y_val, val_preds)

    # A naive baseline: just predict each player's avg_points_last_5 directly,
    # no model at all. If our model can't beat this, something's wrong.
    baseline_preds = val_df["avg_points_last_5"].fillna(val_df["target"].mean())
    baseline_mae = mean_absolute_error(y_val, baseline_preds)

    print(f"\nModel MAE:    {mae:.3f}")
    print(f"Baseline MAE: {baseline_mae:.3f}  (predicting avg_points_last_5 directly)")

    import os
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    return model, mae, baseline_mae


if __name__ == "__main__":
    train()