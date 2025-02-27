# USDA Weekly Egg Inventory Data Pipeline

This document describes the process of fetching USDA weekly egg inventory data and loading it into a Snowflake database. The pipeline consists of two main components: a data fetching script and a data loading script.

## Data Source

The data is sourced from the USDA Agricultural Marketing Service's public API:
- Report ID: 1427 (National Weekly Shell Egg Inventory)
- Date Range: January 1, 2024 to February 28, 2025
- API Endpoint: https://mymarketnews.ams.usda.gov/public_data/ajax-search-data-by-report/1427

## Scripts Overview

### 1. fetch_egg_data.py

A Python CLI tool that fetches egg inventory data from the USDA API and saves it to a CSV file.

#### Features:
- Monthly pagination to handle API's 1000-row limit
- Configurable report ID and date range
- Proper HTTP headers for API requests
- Progress reporting and error handling
- CSV output with standardized fields

#### Usage:
```bash
python fetch_egg_data.py \
    --report-id 1427 \
    --start-date "01/01/2024" \
    --end-date "02/28/2025" \
    --output egg_inventory.csv
```

### 2. load_to_snowflake.py

A Python script that loads the CSV data into Snowflake using batch inserts.

#### Features:
- Batch processing for efficient data loading
- Error handling and logging
- Data integrity verification
- Uses Snowflake Python connector

#### Usage:
```bash
python load_to_snowflake.py \
    --input egg_inventory.csv \
    --table shadowfax.public.usda_weekly_egg_inventory
```

## Database Schema

The data is stored in a transient Snowflake table with the following schema:

```sql
CREATE TRANSIENT TABLE shadowfax.public.usda_weekly_egg_inventory (
    report_date DATE NOT NULL,
    region VARCHAR(50) NOT NULL,
    egg_class VARCHAR(50) NOT NULL,
    volume_30doz_cases_thousands FLOAT,
    pct_change_from_last_week FLOAT,
    inserted_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

## Data Processing Steps

1. **Data Fetching**:
   - Script fetches data month by month to handle API pagination
   - Each API response is validated and transformed
   - Data is accumulated and written to CSV
   - Total records fetched: 4,758

2. **Data Loading**:
   - CSV data is read in batches
   - Each batch is validated and transformed as needed
   - Data is inserted into Snowflake using batch operations
   - All 4,758 records were successfully loaded

## Data Verification

The loaded data was verified for:
- Date range coverage (Jan 1, 2024 to Feb 24, 2025)
- Completeness of regions (7 unique regions)
- Completeness of egg classes (12 unique classes)
- Data type consistency
- No duplicate records

## Notes

- The API returns data in chunks of 1000 rows maximum
- Volume is measured in "30-dozen cases thousands"
- Egg class and type were combined into a single field
- All rows from the CSV were successfully loaded into Snowflake
- The table is created as transient to avoid storage costs for historical data