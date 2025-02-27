-- Create a transient table for USDA weekly egg inventory data
CREATE OR REPLACE TRANSIENT TABLE SHADOWFAX.DEV.usda_weekly_egg_inventory (
    report_date DATE NOT NULL,
    region VARCHAR(50) NOT NULL,
    egg_type VARCHAR(100) NOT NULL,  -- Combined egg class/type field
    volume_30doz_cases_thousands DECIMAL(10, 2),  -- Volume in thousands of 30-dozen cases
    percent_change_last_week DECIMAL(5, 2),  -- Percentage change from previous week
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);