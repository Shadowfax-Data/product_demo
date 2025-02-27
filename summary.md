# USDA Weekly Shell Egg Inventory Data Processing

This project processes and visualizes USDA's National Weekly Shell Egg Inventory data from January 2024 to February 2025. It includes scripts for data fetching, database loading, and visualization.

## Project Components

### 1. Data Fetching (`fetch_egg_data.py`)

A Python CLI tool that fetches egg inventory data from the USDA API with the following features:
- Handles pagination by month to work around the 1000-row API limit
- Provides configurable parameters for report ID, date range, and output path
- Combines egg class/type fields for cleaner data structure
- Includes all required HTTP headers for API authentication

Usage:
```bash
python fetch_egg_data.py \
    --report-id 1427 \
    --start-date "2024-01-01" \
    --end-date "2025-02-28" \
    --output egg_inventory_data.csv
```

### 2. Database Schema (`create_egg_inventory_table.sql`)

Creates a transient Snowflake table with the following structure:
```sql
CREATE OR REPLACE TRANSIENT TABLE SHADOWFAX.DEV.usda_weekly_egg_inventory (
    report_date DATE NOT NULL,
    region VARCHAR(50) NOT NULL,
    egg_type VARCHAR(50) NOT NULL,
    volume DECIMAL(10,2) NOT NULL,
    pct_change_last_week DECIMAL(5,2),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

Key features:
- Combines egg class/type into a single field
- Uses appropriate data types for each column
- Includes NOT NULL constraints on key fields
- Adds timestamp for data lineage

### 3. Data Loading (`load_to_snowflake.py`)

A Python script that loads the CSV data into Snowflake with:
- Batch insert functionality for efficient data loading
- Error handling and logging
- Data validation and transformation
- Progress tracking

Usage:
```bash
python load_to_snowflake.py \
    --input egg_inventory_data.csv \
    --batch-size 1000
```

### 4. Data Visualization (`plot_inventory.py`)

Creates a matplotlib visualization showing egg inventory trends:
- Line plot of inventory levels by egg type
- Focus on 6-Area totals for different egg types
- Clear formatting with proper labels and legend
- Saves output as PNG file

Usage:
```bash
python plot_inventory.py \
    --start-date "2025-01-01" \
    --end-date "2025-02-28" \
    --output egg_inventory_2025.png
```

## Data Processing Results

1. Data Collection:
   - Successfully retrieved 4,758 records from USDA API
   - Date range: January 1, 2024 to February 28, 2025
   - Complete coverage for all regions and egg types

2. Database Loading:
   - All 4,758 records successfully loaded into Snowflake
   - No data loss or transformation errors
   - Data integrity verified through summary statistics

3. Visualization:
   - Created clear trend visualization for 2025 data
   - Shows inventory levels across different egg types
   - Highlights weekly variations and overall trends

## Dependencies

- Python 3.x
- Required Python packages:
  - requests
  - pandas
  - snowflake-connector-python
  - matplotlib
- Snowflake database access
- USDA API access