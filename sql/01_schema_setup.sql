-- ====================================================================
-- 01_schema_setup.sql: DDL Definition for Retail Store Inventory & Demand
-- Dataset: retail_store_inventory (73,100 records across 5 stores and 20 products)
-- ====================================================================

-- 1. Dimension Table: Products
CREATE TABLE IF NOT EXISTS dim_products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    unit_price NUMERIC(10, 2),
    holding_cost_annual_pct NUMERIC(5, 2),
    order_cost NUMERIC(10, 2),
    lead_time_days INT,
    lead_time_std NUMERIC(5, 2),
    base_demand INT
);

-- 2. Dimension Table: Stores (Optional Normalized Entity)
CREATE TABLE IF NOT EXISTS dim_stores (
    store_id VARCHAR(20) PRIMARY KEY,
    store_name VARCHAR(100),
    region VARCHAR(50)
);

-- 3. Fact Table: Daily Store Sales & Inventory Transactions
CREATE TABLE IF NOT EXISTS fact_sales_inventory (
    date DATE NOT NULL,
    store_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(20) NOT NULL REFERENCES dim_products(product_id),
    category VARCHAR(50),
    region VARCHAR(50),
    inventory_on_hand INT,
    units_sold INT,
    units_ordered INT,
    demand_forecast NUMERIC(10, 2),
    unit_price NUMERIC(10, 2),
    discount_pct NUMERIC(5, 2),
    weather_condition VARCHAR(50),
    is_promoted INT,
    competitor_price NUMERIC(10, 2),
    seasonality VARCHAR(50),
    revenue NUMERIC(12, 2),
    stockout_flag INT,
    lost_demand INT,
    latent_demand INT,
    PRIMARY KEY (date, store_id, product_id)
);

-- Create performance indexes for common analytical queries
CREATE INDEX IF NOT EXISTS idx_sales_date ON fact_sales_inventory(date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON fact_sales_inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_store ON fact_sales_inventory(store_id);
