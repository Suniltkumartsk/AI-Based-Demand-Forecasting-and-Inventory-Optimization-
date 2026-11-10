# Power BI DAX Formulas and Measures Guide
# Project: AI-Based Demand Forecasting & Inventory Optimization
# Dataset: retail_store_inventory

## 1. Core Inventory & Sales KPIs

### Total On-Hand Inventory
```dax
Total OnHand Units = SUM('test_predictions'[inventory_on_hand])
```

### Total Sales Revenue ($)
```dax
Total Revenue = SUM('test_predictions'[revenue])
```

### Total Actual Units Sold
```dax
Total Actual Units = SUM('test_predictions'[units_sold])
```

### Total Forecast Units
```dax
Total Forecast Units = SUM('test_predictions'[forecast_units])
```

### Total Lost Revenue from Stockouts ($)
```dax
Lost Revenue = 
SUMX(
    'test_predictions',
    'test_predictions'[lost_demand] * 'test_predictions'[unit_price]
)
```

---

## 2. Forecast Performance Measures

### Weighted Absolute Percentage Error (WAPE)
```dax
WAPE = 
DIVIDE(
    SUMX('test_predictions', ABS('test_predictions'[units_sold] - 'test_predictions'[forecast_units])),
    [Total Actual Units],
    0
)
```
*(Format as Percentage: `0.0%`)*

### Forecast Accuracy %
```dax
Forecast Accuracy % = 
MAX(0, 1 - [WAPE])
```
*(Format as Percentage: `0.0%`)*

### Forecast Tracking Signal / Bias
```dax
Forecast Bias = 
DIVIDE(
    SUMX('test_predictions', 'test_predictions'[forecast_units] - 'test_predictions'[units_sold]),
    COUNTROWS('test_predictions'),
    0
)
```

---

## 3. Inventory Optimization & Reorder Triggers

### Dynamic Stock Health Badge (Calculated Column in `inventory_parameters`)
```dax
Stock Status = 
VAR CurrentStock = LOOKUPVALUE(
    'test_predictions'[inventory_on_hand], 
    'test_predictions'[product_id], 'inventory_parameters'[product_id],
    'test_predictions'[date], MAX('test_predictions'[date])
)
VAR SS = 'inventory_parameters'[safety_stock]
VAR ROP = 'inventory_parameters'[reorder_point]
RETURN
    SWITCH(
        TRUE(),
        CurrentStock <= 0, "Stockout",
        CurrentStock <= SS, "Critical",
        CurrentStock <= ROP, "Reorder Needed",
        "Healthy"
    )
```

### Recommended Order Units (PO Size)
```dax
Recommended Order Qty = 
VAR CurrentStock = LOOKUPVALUE(
    'test_predictions'[inventory_on_hand], 
    'test_predictions'[product_id], 'inventory_parameters'[product_id],
    'test_predictions'[date], MAX('test_predictions'[date])
)
VAR ROP = 'inventory_parameters'[reorder_point]
VAR EOQ = 'inventory_parameters'[economic_order_qty]
RETURN
    IF(CurrentStock <= ROP, EOQ, 0)
```
