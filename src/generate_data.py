import os
import numpy as np
import pandas as pd

def process_retail_store_inventory():
    """
    Parses and standardizes retail_store_inventory.csv into clean raw dimensional
    and fact tables (products.csv and sales_inventory.csv) in data/raw/.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    # Check root first, then data/raw
    source_candidates = [
        os.path.join(base_dir, "retail_store_inventory.csv"),
        os.path.join(raw_dir, "retail_store_inventory.csv")
    ]
    
    source_file = None
    for cand in source_candidates:
        if os.path.exists(cand):
            source_file = cand
            break
            
    if not source_file:
        raise FileNotFoundError("Could not find retail_store_inventory.csv in project root or data/raw/")
        
    print(f"Reading dataset from: {source_file}")
    df = pd.read_csv(source_file)
    print(f"Total rows loaded: {len(df):,}")
    
    # 1. Generate dim_products (products.csv)
    lead_time_map = {
        "Groceries": (3, 0.6),
        "Clothing": (7, 1.0),
        "Toys": (7, 1.2),
        "Electronics": (10, 1.4),
        "Furniture": (14, 1.8)
    }
    
    products = []
    for pid in sorted(df["Product ID"].unique()):
        sub = df[df["Product ID"] == pid]
        top_cat = sub["Category"].value_counts().index[0]
        avg_price = round(float(sub["Price"].mean()), 2)
        daily_demand = sub.groupby("Date")["Units Sold"].sum().mean()
        lt_mean, lt_std = lead_time_map.get(top_cat, (7, 1.0))
        order_cost = round(float(40.0 + (int(pid[1:]) * 2.0)), 2)
        products.append({
            "product_id": pid,
            "product_name": f"{pid} ({top_cat})",
            "category": top_cat,
            "unit_price": avg_price,
            "holding_cost_annual_pct": 0.20,
            "order_cost": order_cost,
            "lead_time_days": lt_mean,
            "lead_time_std": lt_std,
            "base_demand": int(round(daily_demand))
        })
        
    df_products = pd.DataFrame(products)
    products_out = os.path.join(raw_dir, "products.csv")
    df_products.to_csv(products_out, index=False)
    print(f"Exported products metadata -> {products_out} ({len(df_products)} products)")
    
    # 2. Standardize fact_sales_inventory (sales_inventory.csv)
    df_sales = pd.DataFrame()
    df_sales["date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    df_sales["store_id"] = df["Store ID"]
    df_sales["product_id"] = df["Product ID"]
    df_sales["category"] = df["Category"]
    df_sales["region"] = df["Region"]
    df_sales["inventory_on_hand"] = df["Inventory Level"]
    df_sales["units_sold"] = df["Units Sold"]
    df_sales["units_ordered"] = df["Units Ordered"]
    df_sales["demand_forecast"] = df["Demand Forecast"]
    df_sales["unit_price"] = df["Price"]
    df_sales["discount_pct"] = df["Discount"]
    df_sales["weather_condition"] = df["Weather Condition"]
    df_sales["is_promoted"] = df["Holiday/Promotion"]
    df_sales["competitor_price"] = df["Competitor Pricing"]
    df_sales["seasonality"] = df["Seasonality"]
    
    # Supply chain calculated metrics
    df_sales["revenue"] = np.round(df_sales["units_sold"] * df_sales["unit_price"] * (1 - df_sales["discount_pct"] / 100.0), 2)
    df_sales["stockout_flag"] = (df_sales["units_sold"] >= df_sales["inventory_on_hand"]).astype(int)
    df_sales["lost_demand"] = np.where(
        df_sales["stockout_flag"] == 1,
        np.maximum(0, np.round(df_sales["demand_forecast"] - df_sales["units_sold"])).astype(int),
        0
    )
    df_sales["latent_demand"] = df_sales["units_sold"] + df_sales["lost_demand"]
    
    # Ensure sorted by date, store, and product
    df_sales = df_sales.sort_values(["date", "store_id", "product_id"]).reset_index(drop=True)
    sales_out = os.path.join(raw_dir, "sales_inventory.csv")
    df_sales.to_csv(sales_out, index=False)
    print(f"Exported sales & inventory records -> {sales_out} ({len(df_sales):,} records)")

if __name__ == "__main__":
    process_retail_store_inventory()
