# USDA Weekly Egg Inventory Data Pipeline

This project implements a data pipeline to fetch, process, and store USDA Weekly Shell Egg Inventory data in a Snowflake database. The pipeline consists of two main components: a data downloader and a data loader.

## Components

### 1. Data Downloader (`usda_egg_inventory_downloader.py`)

A Python CLI tool that fetches egg inventory data from the USDA Market News API.

#### Usage

```bash
python usda_egg_inventory_downloader.py [options]

Options:
  --report-id INTEGER    Report ID (default: 1427 - National Weekly Shell Egg Inventory)
  --start-date TEXT     Start date in MM/DD/YYYY format (default: 01/01/2024)
  --end-date TEXT       End date in MM/DD/YYYY format (default: current date)
  --output TEXT         Output CSV file path (default: egg_inventory_data.csv)
```

#### Features
- Configurable date range and report ID
- Proper HTTP headers for API requests
- JSON response parsing and CSV conversion
- Error handling and date validation
- Progress reporting

### 2. Snowflake Table Schema

The data is stored in a transient Snowflake table `shadowfax.public.usda_weekly_egg_inventory` with the following schema:

```sql
CREATE TRANSIENT TABLE shadowfax.public.usda_weekly_egg_inventory (
    report_date DATE NOT NULL,
    region VARCHAR NOT NULL,
    egg_type VARCHAR NOT NULL,
    egg_class VARCHAR NOT NULL,
    package_type VARCHAR,
    volume NUMERIC,
    volume_change_prev_week NUMERIC,
    percent_change_prev_week NUMERIC,
    commodity VARCHAR,
    market_type VARCHAR,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (report_date, region, egg_type, egg_class)
);
```

### 3. Data Loader (`snowflake_loader.py`)

A Python script that loads the CSV data into Snowflake.

#### Usage

```bash
python snowflake_loader.py [input_file]

Arguments:
  input_file    Path to the CSV file (default: egg_inventory_data.csv)
```

#### Features
- Snowflake connection management using environment variables
- Batch loading for better performance
- Error handling and logging
- Data validation before loading

## Environment Setup

The following environment variables are required for Snowflake connection:

```bash
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PASSWORD
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
SNOWFLAKE_SCHEMA
```

## Data Processing Steps

1. **Data Collection**:
   - The downloader script fetches data from the USDA Market News API
   - Data is retrieved for the National Weekly Shell Egg Inventory report (ID: 1427)
   - The API response includes inventory volumes and changes from the previous week

2. **Data Transformation**:
   - JSON response is parsed and flattened
   - Data is structured into a normalized format
   - Dates are standardized to DATE format
   - Numeric values are properly typed

3. **Data Loading**:
   - CSV data is validated before loading
   - Data is loaded in batches for efficiency
   - Primary key constraints ensure data integrity
   - Timestamps are automatically added for tracking

## Data Quality Checks

- Date range validation in the downloader
- Data type validation before loading
- Primary key constraints in Snowflake
- Automatic duplicate handling
- Error logging and reporting

## Maintenance and Monitoring

- The transient table automatically manages storage
- Loading errors are logged for troubleshooting
- Process can be automated via scheduling
- Data freshness can be monitored via created_at timestamp