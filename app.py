import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import math
import os

# =============================================================
# 1. PAGE SETUP & THEME
# =============================================================
st.set_page_config(
    page_title="AI Demand Forecasting & Inventory Optimization",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme support for Altair charts
try:
    alt.theme.enable("dark")
except AttributeError:
    alt.themes.enable("dark")

# Modern glassmorphism dark styling
st.markdown("""
<style>
    .stApp { background: linear-gradient(160deg, #0b1120 0%, #111827 40%, #0f172a 100%); }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid #1e293b;
    }
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { color: #cbd5e1; }

    /* Glass Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.55);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 16px;
        padding: 20px 22px;
        min-height: 130px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        border-color: rgba(56, 189, 248, 0.35);
        transform: translateY(-2px);
    }

    /* KPI Card Elements */
    .kpi-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
    .kpi-icon {
        width: 38px; height: 38px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem; flex-shrink: 0;
    }
    .kpi-icon.revenue  { background: rgba(74, 222, 128, 0.15); }
    .kpi-icon.accuracy { background: rgba(56, 189, 248, 0.15); }
    .kpi-icon.units    { background: rgba(167, 139, 250, 0.15); }
    .kpi-icon.lost     { background: rgba(248, 113, 113, 0.15); }
    .kpi-icon.alerts   { background: rgba(251, 191, 36, 0.15); }

    .kpi-label { color: #94a3b8; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-value { color: #f1f5f9; font-size: 1.85rem; font-weight: 800; line-height: 1.1; }
    .kpi-delta { font-size: 0.78rem; font-weight: 500; margin-top: 6px; }

    /* Status Colors */
    .delta-green { color: #4ade80; }
    .delta-amber { color: #fbbf24; }
    .delta-red   { color: #f87171; }
    .delta-muted { color: #64748b; }

    /* Tooltip & Badges */
    .info-icon {
        display: inline-flex; align-items: center; justify-content: center;
        width: 18px; height: 18px; border-radius: 50%;
        background: rgba(148, 163, 184, 0.12); color: #94a3b8;
        font-size: 0.65rem; font-weight: 700; cursor: help;
    }
    .section-badge {
        padding: 3px 10px; border-radius: 9999px; font-size: 0.72rem; font-weight: 600;
        background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25);
    }
    .guide-box {
        background: rgba(15, 23, 42, 0.65); border-left: 3px solid #38bdf8;
        padding: 12px 16px; border-radius: 0 10px 10px 0; margin-bottom: 18px;
        color: #94a3b8; font-size: 0.85rem; line-height: 1.5;
    }
    .guide-box b { color: #cbd5e1; }
    .concept-card {
        background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 10px; padding: 14px; margin-bottom: 12px;
    }
    .concept-title { color: #38bdf8; font-weight: 700; font-size: 0.9rem; margin-bottom: 4px; }
    .concept-body { color: #94a3b8; font-size: 0.82rem; line-height: 1.5; }
    .footer-bar {
        text-align: center; color: #475569; font-size: 0.75rem;
        padding: 24px 0 12px 0; border-top: 1px solid rgba(148, 163, 184, 0.08); margin-top: 32px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================
# 2. HELPER FUNCTIONS (Formatting & KPI Cards)
# =============================================================
def fmt_inr(value, full=False):
    """
    Format Indian Rupee values (₹):
    - When full=True: exact amount with 2 decimal places (paisa), e.g. ₹40,748,434.43
    - When full=False: compact readable format, e.g. ₹4.07 Cr or ₹12.5K
    """
    sign = "-" if value < 0 else ""
    abs_v = abs(value)
    if full:
        return f"{sign}₹{abs_v:,.2f}"
    if abs_v >= 1e7:
        return f"{sign}₹{abs_v/1e7:.2f} Cr"
    elif abs_v >= 1e5:
        return f"{sign}₹{abs_v/1e5:.2f} L"
    elif abs_v >= 1e3:
        return f"{sign}₹{abs_v/1e3:.1f}K"
    return f"{sign}₹{abs_v:,.2f}"

def fmt_units(value, full=False):
    """Format volume counts into K/M or full comma separation."""
    if full:
        return f"{int(value):,}"
    abs_v = abs(value)
    if abs_v >= 1e6:
        return f"{value/1e6:.2f}M"
    elif abs_v >= 1e3:
        return f"{value/1e3:.1f}K"
    return f"{int(value):,}"

def render_kpi(col, title, value, delta_text, delta_color, icon, category, tooltip, val_style=""):
    """Render a clean, responsive glassmorphism KPI card in a Streamlit column."""
    with col:
        st.markdown(f"""
        <div class="glass-card">
            <div class="kpi-header">
                <div class="kpi-icon {category}">{icon}</div>
                <div style="flex-grow: 1;">
                    <div class="kpi-label">{title}</div>
                </div>
                <span class="info-icon" title="{tooltip}">i</span>
            </div>
            <div class="kpi-value" {val_style}>{value}</div>
            <div class="kpi-delta {delta_color}">{delta_text}</div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================
# 3. DATA LOADING & CACHING
# =============================================================
@st.cache_data
def load_data():
    """Load predictions, inventory parameters, and product metadata."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    preds_file = os.path.join(base_dir, "data", "processed", "test_predictions.csv")
    params_file = os.path.join(base_dir, "data", "processed", "inventory_parameters.csv")
    prods_file = os.path.join(base_dir, "data", "raw", "products.csv")

    df_preds = pd.read_csv(preds_file)
    df_preds["date"] = pd.to_datetime(df_preds["date"])

    df_params = pd.read_csv(params_file)
    df_prods = pd.read_csv(prods_file)

    # Merge product details into parameters
    cols = ["product_id", "category", "unit_price", "lead_time_days", "lead_time_std", "order_cost", "holding_cost_annual_pct"]
    avail = [c for c in cols if c in df_prods.columns]
    overlap = [c for c in avail if c in df_params.columns and c != "product_id"]
    if overlap:
        df_params = df_params.drop(columns=overlap)
    df_params = df_params.merge(df_prods[avail], on="product_id", how="left")

    return df_preds, df_params

try:
    df_preds, df_params = load_data()
except Exception as e:
    st.error(f"Error loading processed data: {e}")
    st.info("Run `python src/train_and_optimize.py` first to generate processed datasets.")
    st.stop()


# =============================================================
# 4. SIDEBAR CONTROLS & INTERACTIVE FILTERS
# =============================================================
st.sidebar.markdown("### 📦 Supply Chain Control Tower")
st.sidebar.caption("Retail Inventory Analytics • 73,100 records • 5 stores • 20 SKUs")
st.sidebar.markdown("---")

# Filter 1: Store View
view_type = st.sidebar.radio(
    "Analytics View",
    ["Store Network Level", "Single Store Deep-Dive"],
    horizontal=True,
    help="Consolidated totals across all branches or zoom into a specific store."
)

has_store = "store_id" in df_preds.columns
if view_type == "Single Store Deep-Dive" and has_store:
    store_options = sorted(df_preds["store_id"].dropna().unique().tolist())
    selected_store = st.sidebar.selectbox("Store Location", store_options)
else:
    selected_store = "All Stores"

# Filter 2: Region
if selected_store == "All Stores" and "region" in df_preds.columns:
    all_regions = ["All Regions"] + sorted(df_preds["region"].dropna().unique().tolist())
    selected_region = st.sidebar.selectbox("Region", all_regions)
else:
    selected_region = "All Regions"

# Filter 3: Category
all_cats = ["All Categories"] + sorted(df_params["category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Category", all_cats)

if selected_category == "All Categories":
    filtered_prods = df_params
else:
    filtered_prods = df_params[df_params["category"] == selected_category]

# Filter 4: SKU Product
all_pids = ["All Products"] + sorted(filtered_prods["product_id"].unique().tolist())
selected_prod_id = st.sidebar.selectbox("SKU / Product", all_pids)

# Filter 5: Date Range
min_date = df_preds["date"].min().date()
max_date = df_preds["date"].max().date()
date_range = st.sidebar.date_input("Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)

# Simulation Parameters
st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚙️ What-If Simulation Engine")
st.sidebar.caption("Simulate supplier delays and service level targets.")

sim_service_level = st.sidebar.select_slider(
    "Target Service Level (CSL)",
    options=[0.90, 0.95, 0.98, 0.99],
    value=0.95,
    format_func=lambda x: f"{int(x*100)}%",
    help="Target probability of not stocking out during supplier lead time."
)

lead_time_buffer = st.sidebar.slider(
    "Supplier Delay (± Days)", -3, 7, 0,
    help="Simulate shipping delays. Positive days increase safety stock."
)

order_cost_multiplier = st.sidebar.slider(
    "Order Cost Multiplier", 0.5, 2.0, 1.0, 0.1,
    help="Higher ordering cost makes EOQ batch sizes larger."
)

# Apply filters to predictions
filtered_preds = df_preds.copy()
if has_store and selected_store != "All Stores":
    filtered_preds = filtered_preds[filtered_preds["store_id"] == selected_store]
if selected_region != "All Regions" and "region" in filtered_preds.columns:
    filtered_preds = filtered_preds[filtered_preds["region"] == selected_region]
if selected_category != "All Categories":
    cat_pids = df_params[df_params["category"] == selected_category]["product_id"].unique()
    filtered_preds = filtered_preds[filtered_preds["product_id"].isin(cat_pids)]
if selected_prod_id != "All Products":
    filtered_preds = filtered_preds[filtered_preds["product_id"] == selected_prod_id]
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = date_range
    filtered_preds = filtered_preds[(filtered_preds["date"].dt.date >= start_d) & (filtered_preds["date"].dt.date <= end_d)]


# =============================================================
# 5. WHAT-IF INVENTORY OPTIMIZATION MATH
# =============================================================
z_map = {0.90: 1.28, 0.95: 1.645, 0.98: 2.05, 0.99: 2.33}
z_score = z_map.get(sim_service_level, 1.645)
sim_params = filtered_prods.copy()

def recompute_inventory(row):
    """Compute Safety Stock, ROP, and EOQ under active simulation inputs."""
    d_mean = row["avg_daily_demand"]
    d_std = d_mean * 0.25
    l_mean = max(1, row["lead_time_days"] + lead_time_buffer)
    l_std = row["lead_time_std"]

    # Bivariate standard deviation: sqrt( L*s_D^2 + D^2*s_L^2 )
    combined_std = math.sqrt(l_mean * (d_std**2) + (d_mean**2) * (l_std**2))
    safety_stock = int(math.ceil(z_score * combined_std))
    lead_time_demand = d_mean * l_mean
    reorder_point = int(math.ceil(lead_time_demand + safety_stock))

    annual_demand = d_mean * 365
    holding_cost = (row["unit_price"] * 0.6) * row["holding_cost_annual_pct"]
    adj_order_cost = row["order_cost"] * order_cost_multiplier

    if holding_cost > 0:
        eoq = int(math.ceil(math.sqrt((2 * annual_demand * adj_order_cost) / holding_cost)))
    else:
        eoq = int(math.ceil(lead_time_demand))

    return pd.Series([safety_stock, reorder_point, eoq, l_mean], index=["safety_stock", "reorder_point", "economic_order_qty", "sim_lead_time"])

sim_params[["safety_stock", "reorder_point", "economic_order_qty", "sim_lead_time"]] = sim_params.apply(recompute_inventory, axis=1)

# Latest stock snapshot
latest_date = df_preds["date"].max()
latest_df = df_preds[df_preds["date"] == latest_date]
if has_store and selected_store != "All Stores":
    latest_df = latest_df[latest_df["store_id"] == selected_store]

latest_stock = latest_df.groupby("product_id")["inventory_on_hand"].sum().reset_index()
if "inventory_on_hand" in sim_params.columns:
    sim_params = sim_params.drop(columns=["inventory_on_hand"])
sim_params = sim_params.merge(latest_stock, on="product_id", how="left")
sim_params["inventory_on_hand"] = sim_params["inventory_on_hand"].fillna(0).astype(int)

def get_status(row):
    """Categorize inventory health status."""
    stock = row["inventory_on_hand"]
    if stock <= 0:
        return "Stockout"
    elif stock <= row["safety_stock"]:
        return "Critical"
    elif stock <= row["reorder_point"]:
        return "Reorder Needed"
    return "Healthy"

sim_params["Status"] = sim_params.apply(get_status, axis=1)


# =============================================================
# 6. TOP HEADER & KEY METRIC CARDS (With Paisa Toggle)
# =============================================================
st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="font-size: 2rem;">📦</div>
        <div>
            <div style="color: #f1f5f9; font-size: 1.45rem; font-weight: 800;">Demand Forecasting & Inventory Optimization</div>
            <div style="color: #64748b; font-size: 0.8rem;">AI-Powered Retail Supply Chain Intelligence</div>
        </div>
    </div>
    <div class="section-badge">● Live Analytics</div>
</div>
""", unsafe_allow_html=True)

with st.expander("ℹ️  Quick Guide — How to read this dashboard", expanded=False):
    st.markdown("""
    - **Top KPI Cards**: Real-time sales, AI accuracy, physical units, stockout losses, and reorder alerts.
    - **Tab 1 (Forecasting)**: Daily actual demand vs. AI predictions with 7-day smoothing option.
    - **Tab 2 (Inventory)**: Automated procurement matrix with Safety Stock, Reorder Points, and EOQ.
    - **Tab 3 (Demand Drivers)**: Impact of promotions, weather, day-of-week, and pricing.
    - **Tab 4 (Diagnostics)**: Per-SKU error metrics (WAPE, MAE, RMSE, Bias).
    """)

# Compute high-level KPIs
total_actual = filtered_preds["units_sold"].sum()
total_pred = filtered_preds["forecast_units"].sum()
total_rev = filtered_preds["revenue"].sum()
total_lost_units = filtered_preds["lost_demand"].sum()

if "unit_price" in filtered_preds.columns:
    total_lost_rev = (filtered_preds["lost_demand"] * filtered_preds["unit_price"]).sum()
else:
    total_lost_rev = total_lost_units * 55.0

wape = (abs(total_actual - total_pred) / total_actual * 100) if total_actual > 0 else 0
accuracy = max(0, 100 - wape)
critical_items = (sim_params["Status"].isin(["Stockout", "Critical", "Reorder Needed"])).sum()

# Paisa Currency Toggle
kpi_title_col, toggle_col = st.columns([3, 2])
with kpi_title_col:
    st.markdown('<div style="color: #94a3b8; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; padding-top: 8px;">Executive Summary Metrics</div>', unsafe_allow_html=True)
with toggle_col:
    show_full_currency = st.toggle(
        "🪙 Show Full Amount with Paisa",
        value=False,
        help="Turn ON to view exact amounts with paisa (e.g. ₹40,748,434.43). Turn OFF for compact view (e.g. ₹4.07 Cr)."
    )

val_style = 'style="font-size: 1.35rem; white-space: nowrap;"' if show_full_currency else ''

# 5 Top KPI Cards
c1, c2, c3, c4, c5 = st.columns(5)
render_kpi(c1, "Realized Revenue", fmt_inr(total_rev, full=show_full_currency), "▲ Total Sales Realized", "delta-green", "💰", "revenue", "Total fulfilled sales in ₹", val_style)

acc_color = "delta-green" if accuracy >= 90 else ("delta-amber" if accuracy >= 80 else "delta-red")
render_kpi(c2, "AI Accuracy", f"{accuracy:.1f}%", f"WAPE: {wape:.2f}%", acc_color, "🎯", "accuracy", "100% minus WAPE. Above 90% is enterprise-grade.")

render_kpi(c3, "Units Sold", fmt_units(total_actual, full=show_full_currency), f"AI Pred: {fmt_units(total_pred, full=show_full_currency)}", "delta-muted", "📊", "units", "Total items sold across selected filters.")
render_kpi(c4, "Lost Revenue", fmt_inr(total_lost_rev, full=show_full_currency), f"▼ {fmt_units(total_lost_units, full=show_full_currency)} lost units", "delta-red", "⚠️", "lost", "Forfeited revenue due to empty shelves.", val_style)

alert_color = "delta-red" if critical_items > 0 else "delta-green"
alert_msg = f"🔴 {critical_items} SKUs Need PO" if critical_items > 0 else "✅ All SKUs Healthy"
render_kpi(c5, "Reorder Alerts", f"{critical_items} / {len(sim_params)}", alert_msg, alert_color, "🔔", "alerts", "SKUs whose stock dropped below Reorder Point.")

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================
# 7. DASHBOARD TABS
# =============================================================
tab_forecast, tab_inventory, tab_drivers, tab_diagnostics = st.tabs([
    "📈 Demand Forecasting",
    "🛡️ Inventory Optimization",
    "🔍 Demand Drivers",
    "📊 Model Diagnostics"
])

# -------------------------------------------------------------
# TAB 1: DEMAND FORECASTING
# -------------------------------------------------------------
with tab_forecast:
    st.markdown("""
    <div class="guide-box">
        <b>📈 Forecasting View:</b> Compares <b>Actual Customer Demand</b> (blue) with the <b>AI Forecast</b> (green dashed).
        Tight overlap indicates high predictive accuracy. Use 7-day smoothing to filter daily noise.
    </div>
    """, unsafe_allow_html=True)

    t1, t2 = st.columns([3, 1])
    with t1:
        time_agg = st.radio("Aggregation", ["Daily Actuals", "7-Day Moving Average"], horizontal=True, label_visibility="collapsed")
    with t2:
        st.caption("💡 7-day rolling view reveals underlying seasonal trends.")

    daily_agg = filtered_preds.groupby("date")[["units_sold", "forecast_units", "lost_demand"]].sum().reset_index()
    if time_agg == "7-Day Moving Average":
        daily_agg["units_sold"] = daily_agg["units_sold"].rolling(7, min_periods=1).mean()
        daily_agg["forecast_units"] = daily_agg["forecast_units"].rolling(7, min_periods=1).mean()

    daily_melted = daily_agg.melt(id_vars=["date"], value_vars=["units_sold", "forecast_units"], var_name="Type", value_name="Units")
    daily_melted["Type"] = daily_melted["Type"].map({"units_sold": "Actual Demand", "forecast_units": "AI Forecast"})

    # Demand line chart with area shading
    area_chart = alt.Chart(daily_melted).mark_area(opacity=0.08).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("Units:Q", title="Demand Units"),
        color=alt.Color("Type:N", scale=alt.Scale(domain=["Actual Demand", "AI Forecast"], range=["#38bdf8", "#4ade80"]), legend=None)
    )
    line_chart = alt.Chart(daily_melted).mark_line(strokeWidth=2).encode(
        x=alt.X("date:T"),
        y=alt.Y("Units:Q"),
        color=alt.Color("Type:N", scale=alt.Scale(domain=["Actual Demand", "AI Forecast"], range=["#38bdf8", "#4ade80"]), legend=alt.Legend(orient="top", title=None)),
        strokeDash=alt.condition(alt.datum.Type == "AI Forecast", alt.value([6, 4]), alt.value([0])),
        tooltip=[alt.Tooltip("date:T", title="Date"), alt.Tooltip("Type:N", title="Series"), alt.Tooltip("Units:Q", format=",.1f", title="Units")]
    )
    st.altair_chart((area_chart + line_chart).properties(height=360).interactive(), use_container_width=True)

    # Lost demand timeline
    if daily_agg["lost_demand"].sum() > 0:
        st.markdown('<div style="margin: 16px 0 8px 0; font-weight: 700; color: #f87171;">⚠️ Stockout Impact Timeline (Lost Demand Units)</div>', unsafe_allow_html=True)
        lost_chart = alt.Chart(daily_agg).mark_area(
            color=alt.Gradient(gradient="linear", stops=[alt.GradientStop(color="rgba(248,113,113,0.35)", offset=0), alt.GradientStop(color="rgba(248,113,113,0.02)", offset=1)], x1=0, x2=0, y1=0, y2=1),
            line={"color": "#f87171", "strokeWidth": 1.5}
        ).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("lost_demand:Q", title="Lost Demand"),
            tooltip=[alt.Tooltip("date:T"), alt.Tooltip("lost_demand:Q", format=",", title="Lost Units")]
        ).properties(height=140)
        st.altair_chart(lost_chart, use_container_width=True)

    # Store performance comparison
    if selected_store == "All Stores" and has_store:
        st.markdown("---")
        st.markdown('<div style="font-weight: 700; color: #f1f5f9; margin-bottom: 8px;">🏬 Store Performance Comparison</div>', unsafe_allow_html=True)
        store_vol = filtered_preds.groupby("store_id").agg(
            total_sales=("units_sold", "sum"),
            revenue=("revenue", "sum")
        ).reset_index()

        sc1, sc2 = st.columns(2)
        with sc1:
            st.altair_chart(alt.Chart(store_vol).mark_bar(cornerRadius=6, color="#38bdf8").encode(
                x=alt.X("store_id:N", title="Store"), y=alt.Y("total_sales:Q", title="Units Sold"),
                tooltip=["store_id:N", alt.Tooltip("total_sales:Q", format=",", title="Units Sold")]
            ).properties(height=240), use_container_width=True)
        with sc2:
            st.altair_chart(alt.Chart(store_vol).mark_bar(cornerRadius=6, color="#4ade80").encode(
                x=alt.X("store_id:N", title="Store"), y=alt.Y("revenue:Q", title="Revenue (₹)"),
                tooltip=["store_id:N", alt.Tooltip("revenue:Q", format=",.0f", title="Revenue (₹)")]
            ).properties(height=240), use_container_width=True)

# -------------------------------------------------------------
# TAB 2: INVENTORY OPTIMIZATION
# -------------------------------------------------------------
with tab_inventory:
    st.markdown("""
    <div class="guide-box">
        <b>🛡️ Inventory Rules:</b><br>
        • <b>Safety Stock (SS)</b>: Minimum buffer kept to absorb unexpected spikes and shipping delays.<br>
        • <b>Reorder Point (ROP)</b>: When stock drops below this level, a new order must be placed.<br>
        • <b>EOQ</b>: The ideal purchase batch size that minimizes combined ordering and holding costs.
    </div>
    """, unsafe_allow_html=True)

    sim_text = f"Active Simulation: CSL {int(sim_service_level*100)}% (Z={z_score}) | Lead Time Buffer: {lead_time_buffer:+d} days | Order Cost: {order_cost_multiplier:.1f}x"
    st.markdown(f'<div style="margin-bottom: 12px;"><span class="section-badge">{sim_text}</span></div>', unsafe_allow_html=True)

    # Status distribution charts
    status_counts = sim_params["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    status_colors = alt.Scale(domain=["Healthy", "Reorder Needed", "Critical", "Stockout"], range=["#4ade80", "#fbbf24", "#f87171", "#ef4444"])

    s1, s2 = st.columns([1, 2])
    with s1:
        st.altair_chart(alt.Chart(status_counts).mark_arc(innerRadius=45, outerRadius=75).encode(
            theta=alt.Theta("Count:Q"), color=alt.Color("Status:N", scale=status_colors, legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["Status:N", "Count:Q"]
        ).properties(height=200), use_container_width=True)
    with s2:
        st.altair_chart(alt.Chart(status_counts).mark_bar(cornerRadius=6).encode(
            x=alt.X("Status:N", sort=["Healthy", "Reorder Needed", "Critical", "Stockout"], title="Status"),
            y=alt.Y("Count:Q", title="Number of SKUs"),
            color=alt.Color("Status:N", scale=status_colors, legend=None),
            tooltip=["Status:N", "Count:Q"]
        ).properties(height=200), use_container_width=True)

    # Reorder table
    st.markdown("#### 📋 Procurement & Reorder Matrix")
    display_cols = ["product_id", "product_name", "category", "unit_price", "inventory_on_hand", "safety_stock", "reorder_point", "economic_order_qty", "Status"]
    avail_cols = [c for c in display_cols if c in sim_params.columns]
    df_display = sim_params[avail_cols].copy()

    df_display["Recommended Order (Units)"] = df_display.apply(
        lambda r: r["economic_order_qty"] if r["Status"] in ["Reorder Needed", "Critical", "Stockout"] else 0, axis=1
    )
    df_display["Est. Order Cost (₹)"] = df_display["Recommended Order (Units)"] * (df_display["unit_price"] * 0.6)

    df_display = df_display.rename(columns={
        "product_id": "SKU", "product_name": "Product Name", "category": "Category",
        "unit_price": "Unit Price (₹)", "inventory_on_hand": "On-Hand",
        "safety_stock": "Safety Stock", "reorder_point": "ROP", "economic_order_qty": "EOQ", "Status": "Health"
    })

    def color_status(val):
        colors = {"Healthy": "color: #4ade80;", "Reorder Needed": "color: #fbbf24;", "Critical": "color: #f87171;", "Stockout": "color: #ef4444; font-weight: 800;"}
        return colors.get(val, "")

    st.dataframe(df_display.style.map(color_status, subset=["Health"]).format({"Unit Price (₹)": "₹{:.2f}", "Est. Order Cost (₹)": "₹{:,.2f}"}), use_container_width=True, hide_index=True)

    # Summary metrics & CSV export
    total_reorder_cost = df_display["Est. Order Cost (₹)"].sum()
    total_order_units = df_display["Recommended Order (Units)"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Reorder Capital Needed", fmt_inr(total_reorder_cost, full=show_full_currency))
    m2.metric("Total Units to Order", fmt_units(total_order_units, full=show_full_currency))
    with m3:
        csv_data = df_display.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export Procurement Plan (CSV)", csv_data, "procurement_plan.csv", "text/csv")

# -------------------------------------------------------------
# TAB 3: DEMAND DRIVERS
# -------------------------------------------------------------
with tab_drivers:
    st.markdown("""
    <div class="guide-box">
        <b>🔍 Demand Drivers:</b> External signals like promotions, weekend traffic, weather, and competitor pricing
        drive significant demand fluctuations. Understanding these signals prevents unexpected stockouts.
    </div>
    """, unsafe_allow_html=True)

    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**1. Promotional Lift** *(Volume on promo vs regular days)*")
        if "is_promoted" in filtered_preds.columns:
            promo_df = filtered_preds.groupby("is_promoted").agg(avg_units=("units_sold", "mean")).reset_index()
            promo_df["Promotion"] = promo_df["is_promoted"].map({0: "Regular Days", 1: "Promo / Holiday"})
            st.altair_chart(alt.Chart(promo_df).mark_bar(cornerRadius=6).encode(
                x=alt.X("Promotion:N", title=""), y=alt.Y("avg_units:Q", title="Avg Units/Day"),
                color=alt.Color("Promotion:N", scale=alt.Scale(range=["#475569", "#f59e0b"]), legend=None),
                tooltip=["Promotion:N", alt.Tooltip("avg_units:Q", format=".1f")]
            ).properties(height=240), use_container_width=True)

    with d2:
        st.markdown("**2. Day-of-Week Seasonality** *(Weekly shopping habits)*")
        if "day_of_week" in filtered_preds.columns:
            dow_df = filtered_preds.groupby("day_of_week")["units_sold"].mean().reset_index()
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            dow_df["Day"] = dow_df["day_of_week"].map(lambda x: day_names[x] if x < len(day_names) else str(x))
            peak_day = dow_df.loc[dow_df["units_sold"].idxmax(), "Day"]

            st.altair_chart(alt.Chart(dow_df).mark_bar(cornerRadius=6).encode(
                x=alt.X("Day:N", sort=day_names, title=""), y=alt.Y("units_sold:Q", title="Avg Daily Units"),
                color=alt.condition(alt.datum.Day == peak_day, alt.value("#38bdf8"), alt.value("#334155")),
                tooltip=["Day:N", alt.Tooltip("units_sold:Q", format=".1f")]
            ).properties(height=240), use_container_width=True)
            st.caption(f"📊 Peak shopping day: **{peak_day}**")

    d3, d4 = st.columns(2)
    with d3:
        st.markdown("**3. Weather Condition Impact**")
        if "weather_condition" in filtered_preds.columns:
            w_df = filtered_preds.groupby("weather_condition")["units_sold"].mean().reset_index()
            st.altair_chart(alt.Chart(w_df).mark_bar(cornerRadius=6, color="#818cf8").encode(
                x=alt.X("weather_condition:N", title=""), y=alt.Y("units_sold:Q", title="Avg Units"),
                tooltip=["weather_condition:N", alt.Tooltip("units_sold:Q", format=".1f")]
            ).properties(height=240), use_container_width=True)

    with d4:
        st.markdown("**4. Price vs. Competitor Pricing**")
        if "unit_price" in filtered_preds.columns and "competitor_price" in filtered_preds.columns:
            scatter_df = filtered_preds.sample(min(400, len(filtered_preds)))
            st.altair_chart(alt.Chart(scatter_df).mark_circle(size=45, opacity=0.6).encode(
                x=alt.X("unit_price:Q", title="Store Price (₹)"), y=alt.Y("competitor_price:Q", title="Competitor (₹)"),
                color=alt.Color("category:N", title="Category"),
                tooltip=["product_id:N", "unit_price:Q", "competitor_price:Q"]
            ).properties(height=240).interactive(), use_container_width=True)

# -------------------------------------------------------------
# TAB 4: MODEL DIAGNOSTICS
# -------------------------------------------------------------
with tab_diagnostics:
    st.markdown("""
    <div class="guide-box">
        <b>📊 Diagnostic Standards:</b><br>
        • <b>WAPE</b>: Volume-weighted percentage error (supply chain gold standard).<br>
        • <b>Accuracy %</b>: <code>100% - WAPE</code>. Values above 90% indicate enterprise reliability.<br>
        • <b>Forecast Bias</b>: Near-zero is optimal. Positive values provide a safe stockout buffer.
    </div>
    """, unsafe_allow_html=True)

    prod_metrics = []
    for pid, grp in filtered_preds.groupby("product_id"):
        y_true = grp["units_sold"].values
        y_pred = grp["forecast_units"].values
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred)**2))
        wape_p = (np.sum(np.abs(y_true - y_pred)) / np.sum(y_true)) * 100 if np.sum(y_true) > 0 else 0
        bias = np.mean(y_pred - y_true)

        prod_metrics.append({
            "SKU": pid, "Sales (Units)": int(np.sum(y_true)),
            "MAE": round(mae, 2), "RMSE": round(rmse, 2), "WAPE %": round(wape_p, 2),
            "Accuracy": round(max(0, 100 - wape_p), 2), "Bias": round(bias, 2)
        })

    df_metrics = pd.DataFrame(prod_metrics)

    # Accuracy bar chart per SKU
    acc_min = df_metrics["Accuracy"].min()
    st.altair_chart(alt.Chart(df_metrics).mark_bar(cornerRadius=6).encode(
        x=alt.X("SKU:N", sort=alt.EncodingSortField(field="Accuracy", order="descending"), title="Product SKU"),
        y=alt.Y("Accuracy:Q", title="Accuracy %", scale=alt.Scale(domain=[max(0, acc_min - 5), 100])),
        color=alt.condition(alt.datum.Accuracy >= 90, alt.value("#4ade80"), alt.value("#fbbf24")),
        tooltip=["SKU:N", alt.Tooltip("Accuracy:Q", format=".1f", title="Accuracy %"), alt.Tooltip("WAPE %:Q", format=".2f")]
    ).properties(height=240), use_container_width=True)

    m1, m2 = st.columns([3, 2])
    with m1:
        def color_acc(val):
            return "color: #4ade80; font-weight: 700;" if val >= 90 else "color: #fbbf24;"
        st.dataframe(df_metrics.style.map(color_acc, subset=["Accuracy"]), use_container_width=True, hide_index=True)

    with m2:
        st.markdown("""
        <div class="concept-card">
            <div class="concept-title">🎯 Metric Interpretation</div>
            <div class="concept-body">
                <b>• MAE</b>: Average unit error per day.<br>
                <b>• RMSE</b>: Penalizes large outlier errors more heavily.<br>
                <b>• WAPE %</b>: Volume-weighted percentage error.<br>
                <b>• Bias</b>: Positive = slight over-forecast (protects against stockouts).
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("Average Model Accuracy (All SKUs)", f"{df_metrics['Accuracy'].mean():.1f}%")
        st.metric("Average Forecast Bias", f"{df_metrics['Bias'].mean():+.2f} units")

# =============================================================
# FOOTER
# =============================================================
st.markdown("""
<div class="footer-bar">
    AI-Based Retail Demand Forecasting & Inventory Optimization Suite • Currency: Indian Rupee (₹) • Powered by Gradient Boosting ML
</div>
""", unsafe_allow_html=True)
