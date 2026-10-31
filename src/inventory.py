import numpy as np
import pandas as pd
import math

def calculate_inventory_metrics(
    daily_demand_mean: float,
    daily_demand_std: float,
    lead_time_days: float,
    lead_time_std: float,
    unit_cost: float,
    order_cost: float,
    annual_holding_cost_rate: float = 0.20,
    service_level: float = 0.95
):
    """
    Computes Safety Stock, Reorder Point (ROP), and Economic Order Quantity (EOQ).
    
    Service level to Z-score mapping:
    - 90% -> 1.28
    - 95% -> 1.65
    - 98% -> 2.05
    - 99% -> 2.33
    """
    z_scores = {
        0.90: 1.28,
        0.95: 1.645,
        0.98: 2.05,
        0.99: 2.33
    }
    z = z_scores.get(service_level, 1.645)
    
    # Combined variance for variable demand and variable lead time
    # sigma_L_D = sqrt( L * (sigma_D)^2 + (D)^2 * (sigma_L)^2 )
    demand_var = (daily_demand_std ** 2)
    lead_time_var = (lead_time_std ** 2)
    combined_std = math.sqrt(lead_time_days * demand_var + (daily_demand_mean ** 2) * lead_time_var)
    
    safety_stock = int(math.ceil(z * combined_std))
    lead_time_demand = daily_demand_mean * lead_time_days
    reorder_point = int(math.ceil(lead_time_demand + safety_stock))
    
    # Annual Demand D = 365 * daily_demand_mean
    annual_demand = daily_demand_mean * 365
    holding_cost_unit_year = unit_cost * annual_holding_cost_rate
    
    if holding_cost_unit_year > 0:
        eoq = int(math.ceil(math.sqrt((2 * annual_demand * order_cost) / holding_cost_unit_year)))
    else:
        eoq = int(math.ceil(lead_time_demand))
        
    return {
        "service_level": service_level,
        "z_score": z,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "economic_order_qty": eoq,
        "lead_time_demand": round(lead_time_demand, 1)
    }

if __name__ == "__main__":
    # Test sample calculation
    metrics = calculate_inventory_metrics(
        daily_demand_mean=50,
        daily_demand_std=12,
        lead_time_days=7,
        lead_time_std=1.2,
        unit_cost=45.0,
        order_cost=50.0,
        annual_holding_cost_rate=0.20,
        service_level=0.95
    )
    print("Optimization parameters calculated:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
