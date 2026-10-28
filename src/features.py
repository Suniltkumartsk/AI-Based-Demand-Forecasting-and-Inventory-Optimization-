"""
Feature Engineering & Model Evaluation Utilities
------------------------------------------------
This module builds predictive signals for demand forecasting:
1. Calendar features (day of week, month, weekend flags)
2. Past sales lags (what sold yesterday, last week, last month)
3. Rolling statistics (7, 14, and 30-day moving averages)
4. Standard supply chain accuracy metrics (WAPE, MAE, Bias)
"""

import numpy as np
import pandas as pd
from typing import Dict


def create_time_series_features(df: pd.DataFrame, target_col: str = "units_sold") -> pd.DataFrame:
    """
    Transforms raw transactional data into ML-ready time-series features.

    To prevent data leakage, features are calculated separately for each
    [Store, Product] series and only use past information.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # 1. Identify series grouping (Store + Product, or Product only)
    if "store_id" in df.columns:
        group_cols = ["store_id", "product_id"]
    else:
        group_cols = ["product_id"]

    # Sort chronologically so past comes before future
    df = df.sort_values(group_cols + ["date"]).reset_index(drop=True)

    # 2. Calendar Features (Human shopping patterns)
    df["day_of_week"] = df["date"].dt.dayofweek          # 0=Monday, 6=Sunday
    df["day_of_month"] = df["date"].dt.day               # 1 to 31
    df["month"] = df["date"].dt.month                    # 1 to 12
    df["quarter"] = df["date"].dt.quarter                # 1 to 4
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)  # 1 for Saturday/Sunday

    # 3. Lag Features (Sales from 1, 2, 7, 14, 21, and 28 days ago)
    # Example: lag_7 tells the model what sold on the same day last week
    for lag in [1, 2, 7, 14, 21, 28]:
        df[f"lag_{lag}"] = df.groupby(group_cols)[target_col].shift(lag)

    # 4. Rolling Statistics (Moving averages of past sales)
    # We calculate rolling stats on 'lag_1' (yesterday's sales) to guarantee
    # zero future data is leaked into today's prediction
    for window in [7, 14, 30]:
        df[f"rolling_mean_{window}"] = df.groupby(group_cols)["lag_1"].transform(
            lambda s: s.rolling(window, min_periods=window).mean()
        )
        df[f"rolling_std_{window}"] = df.groupby(group_cols)["lag_1"].transform(
            lambda s: s.rolling(window, min_periods=window).std()
        )

    return df


def calculate_forecast_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Evaluates forecasting performance using standard supply chain metrics:
    - MAE: Mean Absolute Error (average unit error per day)
    - RMSE: Root Mean Squared Error (penalizes large outlier mistakes)
    - WAPE: Weighted Absolute Percentage Error (supply chain gold standard)
    - Forecast Accuracy %: 100% - WAPE
    - Bias: Mean difference (positive = slight over-forecast, negative = under-forecast)
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.maximum(0.0, np.array(y_pred, dtype=float))  # No negative demand

    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    total_sales = np.sum(y_true)

    wape = (np.sum(np.abs(y_true - y_pred)) / total_sales) * 100.0 if total_sales > 0 else 0.0
    bias = np.mean(y_pred - y_true)

    return {
        "MAE": round(float(mae), 3),
        "RMSE": round(float(rmse), 3),
        "WAPE_pct": round(float(wape), 2),
        "Forecast_Accuracy_pct": round(float(max(0.0, 100.0 - wape)), 2),
        "Bias": round(float(bias), 3)
    }


if __name__ == "__main__":
    import os

    # Quick test run when executed directly
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sales_file = os.path.join(base_dir, "data", "raw", "sales_inventory.csv")

    if os.path.exists(sales_file):
        print("Testing feature engineering on sample data...")
        sample_df = pd.read_csv(sales_file, nrows=500)
        featured_df = create_time_series_features(sample_df)

        new_features = [c for c in featured_df.columns if c not in sample_df.columns]
        print(f"Successfully generated {len(new_features)} engineered features:")
        print(f"  • Calendar: day_of_week, day_of_month, month, quarter, is_weekend")
        print(f"  • Past Lags: lag_1, lag_2, lag_7, lag_14, lag_21, lag_28")
        print(f"  • Rolling Windows: 7, 14, 30-day means and standard deviations")
    else:
        print(f"Sample file not found at: {sales_file}")
