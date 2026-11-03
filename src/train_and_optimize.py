import os
# Prevent Windows deprecation/wmic warning in joblib/loky
os.environ["LOKY_MAX_CPU_COUNT"] = "4"

import pandas as pd
import numpy as np
from features import create_time_series_features, calculate_forecast_metrics
from inventory import calculate_inventory_metrics
from sklearn.ensemble import HistGradientBoostingRegressor

def run_pipeline():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sales_path = os.path.join(base_dir, "data", "raw", "sales_inventory.csv")
    prod_path = os.path.join(base_dir, "data", "raw", "products.csv")
    
    print("Loading raw sales & inventory data...")
    df_sales = pd.read_csv(sales_path)
    df_prods = pd.read_csv(prod_path)
    
    # Feature Engineering
    print("Generating lag, rolling, and temporal supply chain features...")
    df_featured = create_time_series_features(df_sales, target_col="units_sold")
    
    # Prepare categoricals for HistGradientBoosting native categorical handling
    cat_cols = ["store_id", "product_id", "category", "region", "weather_condition", "seasonality"]
    for col in cat_cols:
        if col in df_featured.columns:
            df_featured[col + "_cat"] = df_featured[col].astype("category")
            
    # Drop initial rows with NaNs due to 28-day lags / 30-day rolling windows
    df_clean = df_featured.dropna().copy()
    
    # Train / Test split by date (last 60 days as out-of-time test set)
    split_date = (pd.to_datetime(df_clean["date"]).max() - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
    train = df_clean[df_clean["date"] <= split_date]
    test = df_clean[df_clean["date"] > split_date].copy()
    
    feature_cols = [
        "demand_forecast", "is_promoted", "discount_pct", "unit_price", "competitor_price", "units_ordered",
        "day_of_week", "day_of_month", "month", "quarter", "is_weekend",
        "lag_1", "lag_2", "lag_7", "lag_14", "lag_21", "lag_28",
        "rolling_mean_7", "rolling_std_7", "rolling_mean_14", "rolling_std_14",
        "rolling_mean_30", "rolling_std_30"
    ]
    
    # Include available categorical features
    for col in cat_cols:
        cat_feature_name = col + "_cat"
        if cat_feature_name in df_clean.columns:
            feature_cols.append(cat_feature_name)
            
    X_train = train[feature_cols]
    y_train = train["units_sold"]
    X_test = test[feature_cols]
    y_test = test["units_sold"]
    
    categorical_mask = [c.endswith("_cat") for c in feature_cols]
    
    print(f"Training Gradient Boosted Regressor on {len(X_train):,} training records across {df_clean['store_id'].nunique()} stores...")
    model = HistGradientBoostingRegressor(
        max_iter=150,
        learning_rate=0.05,
        max_depth=6,
        categorical_features=categorical_mask,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    test["forecast_units"] = np.round(np.maximum(0, preds))
    
    # Model Evaluation
    metrics = calculate_forecast_metrics(y_test.values, preds)
    print("\n--- Model Evaluation (Out-of-Time Test Set: Last 60 Days) ---")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
        
    # Baseline comparison (legacy demand forecast provided in dataset vs actuals)
    if "demand_forecast" in test.columns:
        legacy_metrics = calculate_forecast_metrics(y_test.values, test["demand_forecast"].values)
        print("\n--- Baseline Provided Forecast Comparison ---")
        print(f"  Legacy Baseline Accuracy: {legacy_metrics['Forecast_Accuracy_pct']}% (WAPE: {legacy_metrics['WAPE_pct']}%, MAE: {legacy_metrics['MAE']})")
        print(f"  AI Model Accuracy:        {metrics['Forecast_Accuracy_pct']}% (WAPE: {metrics['WAPE_pct']}%, MAE: {metrics['MAE']})")
        
    # Calculate Inventory Parameters for each product
    print("\n--- Computing Inventory Optimization Parameters ---")
    opt_records = []
    for _, prod in df_prods.iterrows():
        p_id = prod["product_id"]
        p_history = df_sales[df_sales["product_id"] == p_id]
        
        # Per-store daily demand mean and standard deviation
        d_mean = p_history["units_sold"].mean()
        d_std = p_history["units_sold"].std()
        
        inv_params = calculate_inventory_metrics(
            daily_demand_mean=d_mean,
            daily_demand_std=d_std,
            lead_time_days=prod["lead_time_days"],
            lead_time_std=prod["lead_time_std"],
            unit_cost=prod["unit_price"] * 0.6, # assumed acquisition/cogs cost is 60% of retail price
            order_cost=prod["order_cost"],
            annual_holding_cost_rate=prod["holding_cost_annual_pct"],
            service_level=0.95
        )
        inv_params["product_id"] = p_id
        inv_params["product_name"] = prod["product_name"]
        inv_params["avg_daily_demand"] = round(d_mean, 2)
        opt_records.append(inv_params)
        
    df_opt = pd.DataFrame(opt_records)
    
    # Export processed artifacts
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    # Drop categorical columns before CSV export for clean loading
    clean_test_export = test.drop(columns=[c for c in test.columns if c.endswith("_cat")])
    clean_test_export.to_csv(os.path.join(processed_dir, "test_predictions.csv"), index=False)
    df_opt.to_csv(os.path.join(processed_dir, "inventory_parameters.csv"), index=False)
    
    print("\nSample Inventory Optimization Table:")
    print(df_opt[["product_id", "product_name", "avg_daily_demand", "safety_stock", "reorder_point", "economic_order_qty"]].head(10))
    print(f"\nArtifacts successfully exported to: {processed_dir}")

if __name__ == "__main__":
    run_pipeline()
