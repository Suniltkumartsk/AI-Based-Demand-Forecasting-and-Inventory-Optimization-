# Guide: How to Run This Project in Visual Studio Code

This guide walks you through opening, running, debugging, and viewing everything inside VS Code step-by-step.

---

## 1. Open the Project in VS Code

### Option A: From Terminal
Open PowerShell and run:
```powershell
code "c:\Users\admin\Desktop\Projects\ai-demand-forecasting"
```

### Option B: From VS Code UI
1. Launch **Visual Studio Code**.
2. Go to **File** -> **Open Folder...** (or press `Ctrl + K`, `Ctrl + O`).
3. Select the folder:
   `c:\Users\admin\Desktop\Projects\ai-demand-forecasting`
4. Click **Select Folder**.

---

## 2. Set Up the Terminal & Environment

1. Open the integrated terminal in VS Code:
   - Press **`Ctrl + \``** (Ctrl + backtick) or go to **Terminal** -> **New Terminal**.
2. Activate your virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Verify Python packages:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 3. Run the Project Scripts

You can run scripts in two ways:

### Method A: Single-Click Debug / Run (Using F5)
We have pre-configured `.vscode/launch.json`:
1. Press `Ctrl + Shift + D` (or click the **Run & Debug** play icon on the left bar).
2. At the top dropdown, select one of:
   - **`Streamlit: Run Interactive Dashboard`** (Launches the Streamlit app!)
   - **`Python: Train & Optimize Pipeline`**
   - **`Python: Process Retail Inventory Data`**
3. Press **`F5`** (or click the green Play button).

---

### Method B: Run via Integrated Terminal

#### Step 1: Process & Ingest the Retail Store Inventory Dataset
```powershell
python src/generate_data.py
```
*Output*: Reads `retail_store_inventory.csv` (73,100 records) and updates `data/raw/products.csv` (20 products) and `data/raw/sales_inventory.csv` (73,100 clean multi-store records).

#### Step 2: Train Model & Calculate Inventory Optimization
```powershell
python src/train_and_optimize.py
```
*Output*:
- Generates grouped time-series lag and rolling features across all 100 store-product combinations.
- Trains the Gradient Boosted Tree model on 64,100 training records.
- Evaluates out-of-time test set (MAE, RMSE, WAPE %, Forecast Accuracy %).
- Computes Safety Stock, Reorder Point (ROP), and EOQ using bivariate demand and lead-time uncertainty math.
- Exports processed results to `data/processed/test_predictions.csv` and `data/processed/inventory_parameters.csv`.

#### Step 3: Launch the Interactive Streamlit Dashboard
```powershell
streamlit run app.py
```
*Output*: Automatically opens your browser at `http://localhost:8501` featuring:
- Store Location filter (`All Stores`, `S001` - `S005`)
- Category & Product dropdown filters
- Evaluation date range selector
- Dynamic What-If simulation sliders (Target Service Level & Supplier Lead Time buffers)
- Interactive Altair charts for demand trends, seasonality, and promotional surges
- Color-coded replenishment matrix with downloadable procurement CSV orders!

---

## 4. Explore SQL Analysis in VS Code
Open and inspect:
- `sql/01_schema_setup.sql`: Table definitions and indexes.
- `sql/02_demand_patterns.sql`: Multi-store moving averages, promotional lift, weather impact, and stockout queries.
