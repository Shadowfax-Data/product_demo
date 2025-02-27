CREATE OR REPLACE TRANSIENT TABLE shadowfax.dev.usda_weekly_egg_inventory (
    report_date DATE NOT NULL,
    published_date TIMESTAMP_NTZ NOT NULL,
    region VARCHAR(50) NOT NULL,
    egg_type VARCHAR(50),
    egg_class VARCHAR(50),
    volume_cases_thousands DECIMAL(10,2) NOT NULL,
    pct_change_week_over_week DECIMAL(10,2),
    package VARCHAR(100) NOT NULL,
    commodity VARCHAR(50) NOT NULL,
    market_type VARCHAR(50) NOT NULL,
    office_name VARCHAR(100) NOT NULL,
    office_code VARCHAR(20) NOT NULL,
    final_ind VARCHAR(10) NOT NULL,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (report_date, region, egg_type, egg_class)
);