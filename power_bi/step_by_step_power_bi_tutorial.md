# Step-by-Step Power BI Dashboard Tutorial
## AI-Based Demand Forecasting & Inventory Optimization

This tutorial guides you through building an executive-grade Supply Chain & Forecasting dashboard from scratch using the exported CSV files.

---

### Prerequisites & Files Needed
From `ai-demand-forecasting/data/`:
1. `data/raw/products.csv` (Product metadata, lead times, ordering costs)
2. `data/processed/test_predictions.csv` (Daily actual units sold vs. AI model predictions, stockouts, revenue)
3. `data/processed/inventory_parameters.csv` (Precomputed Safety Stock, Reorder Point, and EOQ)

---

## Step 1: Load Data into Power BI Desktop
1. Open **Power BI Desktop**.
2. Click **Get Data** $\rightarrow$ **Text/CSV**.
3. Load the three files:
   - `test_predictions.csv`
   - `inventory_parameters.csv`
   - `products.csv`
4. In the preview window, click **Transform Data** to open the **Power Query Editor**.

---

## Step 2: Data Cleaning & Type Transformations (Power Query)
1. In `test_predictions`:
   - Change `date` column type to **Date**.
   - Ensure `units_sold`, `forecast_units`, `lost_demand`, and `inventory_on_hand` are **Whole Number**.
   - Ensure `revenue` is **Decimal Number** or **Fixed Decimal (Currency)**.
2. In `products` & `inventory_parameters`:
   - Ensure `product_id` is **Text**.
   - Ensure numerical parameters (`safety_stock`, `reorder_point`, `economic_order_qty`, `unit_price`) are appropriate numbers.
3. Click **Close & Apply** in the top-left corner.

---

## Step 3: Establish Data Model Relationships (Model View)
1. Switch to the **Model View** (icon on the left navigation bar).
2. Create standard One-to-Many ($1:*$) relationships:
   - Drag `product_id` from `products` to `product_id` in `test_predictions`.
   - Drag `product_id` from `inventory_parameters` to `product_id` in `test_predictions`.
   - Set Cross-filter direction to **Single**.

---

## Step 4: Write Core DAX Measures
Create a dedicated measures table or right-click `test_predictions` $\rightarrow$ **New Measure**:

### Measure 1: Total Actual Sales Units
```dax
Total Actual Units = SUM(test_predictions[units_sold])
```

### Measure 2: Total Forecast Units
```dax
Total Forecast Units = SUM(test_predictions[forecast_units])
```

### Measure 3: Total Sales Revenue ($)
```dax
Total Revenue = SUM(test_predictions[revenue])
```

### Measure 4: Weighted Absolute Percentage Error (WAPE)
```dax
WAPE = 
DIVIDE(
    SUMX(test_predictions, ABS(test_predictions[units_sold] - test_predictions[forecast_units])),
    [Total Actual Units],
    0
)
```
*(Format this measure as a Percentage: `0.0%`).*

### Measure 5: Forecast Accuracy %
```dax
Forecast Accuracy % = MAX(0, 1 - [WAPE])
```
*(Format this measure as a Percentage: `0.0%`).*

### Measure 6: Total Lost Revenue from Stockouts ($)
```dax
Lost Revenue = 
SUMX(
    test_predictions,
    test_predictions[lost_demand] * RELATED(products[unit_price])
)
```

### Measure 7: Dynamic Stock Health Badge (Calculated Column in `inventory_parameters` or latest snapshot)
Add a **New Column** to `inventory_parameters`:
```dax
Inventory Status = 
VAR CurrentStock = LOOKUPVALUE(
    test_predictions[inventory_on_hand], 
    test_predictions[product_id], inventory_parameters[product_id],
    test_predictions[date], MAX(test_predictions[date])
)
RETURN
    SWITCH(
        TRUE(),
        CurrentStock <= 0, "Stockout",
        CurrentStock <= inventory_parameters[safety_stock], "Critical",
        CurrentStock <= inventory_parameters[reorder_point], "Reorder Needed",
        "Healthy"
    )
```

---

## Step 5: Build Visuals (Report View)

### 1. Canvas Styling & Header
- Set Canvas background to dark slate (`#0F172A`) or light gray (`#F8FAFC`).
- Add a **Text Box** at the top:
  - Title: **Supply Chain & Demand Forecasting Dashboard**
  - Subtitle: *Demand Predictability, Stockout Risk, and Automated Replenishment*

---

### 2. Executive KPI Cards (Top Row)
Add 4 **Card** or **New Card (Preview)** visuals side-by-side:
1. **Card 1 (Total Revenue)**: Field = `[Total Revenue]` (formatted as `$ #,##0`).
2. **Card 2 (Forecast Accuracy)**: Field = `[Forecast Accuracy %]` (Data label color = Green).
3. **Card 3 (WAPE Error)**: Field = `[WAPE]` (formatted as `0.0%`).
4. **Card 4 (Estimated Lost Revenue)**: Field = `[Lost Revenue]` (Data label color = Red).

---

### 3. Visual 1: Line Chart (Actual Demand vs. AI Forecast)
1. Add a **Line Chart**.
2. **X-axis**: Drag `date` from `test_predictions` (switch from Date Hierarchy to exact `date`).
3. **Y-axis**: Drag `[Total Actual Units]` and `[Total Forecast Units]`.
4. Formatting:
   - `Total Actual Units`: Solid line (Teal / Blue).
   - `Total Forecast Units`: Dashed line (Bright Green).
5. **Purpose**: Visually demonstrates how closely the model tracks demand peaks and promotional spikes.

---

### 4. Visual 2: Donut Chart (Inventory Risk Breakdown)
1. Add a **Donut Chart**.
2. **Legend**: Drag `Inventory Status` from `inventory_parameters`.
3. **Values**: Drag `product_id` (Count).
4. Colors:
   - `Healthy` $\rightarrow$ Green (`#4ADE80`)
   - `Reorder Needed` $\rightarrow$ Amber (`#FBBF24`)
   - `Critical` $\rightarrow$ Coral (`#F87171`)
   - `Stockout` $\rightarrow$ Bright Red (`#EF4444`)

---

### 5. Visual 3: Replenishment Decision Matrix (Bottom Table)
1. Add a **Table** visual.
2. Drag in columns:
   - `inventory_parameters[product_id]`
   - `inventory_parameters[product_name]`
   - `inventory_parameters[avg_daily_demand]`
   - `inventory_parameters[safety_stock]`
   - `inventory_parameters[reorder_point]`
   - `inventory_parameters[economic_order_qty]` (Recommended PO size)
   - `inventory_parameters[Inventory Status]`
3. **Conditional Formatting**:
   - Right-click `Inventory Status` field in the Visualizations pane $\rightarrow$ **Conditional formatting** $\rightarrow$ **Background color**.
   - Format based on field values or rules (`Stockout` = Red, `Reorder Needed` = Yellow, `Healthy` = Green).

---

### 6. Visual 4: Product Slicer (Filter Pane)
1. Add a **Slicer** on the side or top.
2. Field: `products[category]` or `products[product_name]`.
3. Set Slicer style to **Dropdown** or **Tile**.
4. Selecting a category dynamically filters both the time-series chart and the replenishment table.

---

## Step 6: Review & Final Polish
- Ensure tooltips show details on hover.
- Save the file as `inventory_forecasting_dashboard.pbix` inside the `power_bi/` directory.
