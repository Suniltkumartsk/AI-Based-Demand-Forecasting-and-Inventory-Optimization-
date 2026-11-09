-- ====================================================================
-- 02_demand_patterns.sql: Analytical Queries to Uncover Patterns & Stockouts
-- Dataset: retail_store_inventory
-- ====================================================================

-- 1. Daily Rolling Demand & Moving Averages (7-day and 30-day by Store & Product)
SELECT 
    date,
    store_id,
    product_id,
    units_sold,
    AVG(units_sold) OVER(
        PARTITION BY store_id, product_id 
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_7d,
    AVG(units_sold) OVER(
        PARTITION BY store_id, product_id 
        ORDER BY date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_30d
FROM fact_sales_inventory
ORDER BY store_id, product_id, date;

-- 2. Day of Week & Monthly Seasonality Profiling across Categories
SELECT 
    category,
    EXTRACT(DOW FROM date) AS day_of_week,
    TO_CHAR(date, 'Day') AS day_name,
    ROUND(AVG(units_sold), 2) AS avg_daily_demand,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM fact_sales_inventory
GROUP BY category, EXTRACT(DOW FROM date), TO_CHAR(date, 'Day')
ORDER BY category, day_of_week;

-- 3. Stockout Impact & Lost Sales Analysis
-- Identifies lost revenue and missed units caused by inventory depletion
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    COUNT(s.date) AS total_days_tracked,
    SUM(s.stockout_flag) AS total_stockout_days,
    SUM(s.lost_demand) AS estimated_lost_units,
    ROUND(SUM(s.lost_demand * s.unit_price), 2) AS estimated_lost_revenue,
    ROUND((SUM(s.stockout_flag)::NUMERIC / COUNT(s.date)) * 100, 2) AS stockout_rate_pct
FROM fact_sales_inventory s
JOIN dim_products p ON s.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY estimated_lost_revenue DESC;

-- 4. Store Performance & Regional Velocity Breakdown
SELECT 
    store_id,
    region,
    COUNT(DISTINCT product_id) AS active_skus,
    SUM(units_sold) AS total_units_sold,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(AVG(units_sold), 2) AS avg_daily_units_per_sku,
    SUM(stockout_flag) AS total_stockouts
FROM fact_sales_inventory
GROUP BY store_id, region
ORDER BY total_revenue DESC;

-- 5. Weather Condition & Promotional Lift Impact
SELECT 
    weather_condition,
    is_promoted,
    ROUND(AVG(units_sold), 2) AS avg_daily_sales,
    ROUND(AVG(revenue), 2) AS avg_daily_revenue,
    COUNT(*) AS sample_size
FROM fact_sales_inventory
GROUP BY weather_condition, is_promoted
ORDER BY avg_daily_sales DESC;
