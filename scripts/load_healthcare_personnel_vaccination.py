import pandas as pd
import snowflake.connector
import os
from typing import Dict, Any

def create_snowflake_connection() -> snowflake.connector.SnowflakeConnection:
    """Create a connection to Snowflake using environment variables."""
    return snowflake.connector.connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'],
        password=os.environ['SNOWFLAKE_PASSWORD'],
        warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
        database='CDC_DATASET',
        schema='PUBLIC',
        role=os.environ['SNOWFLAKE_ROLE']
    )

def create_table(conn: snowflake.connector.SnowflakeConnection) -> None:
    """Create the healthcare personnel vaccination coverage table."""
    create_table_sql = """
    CREATE OR REPLACE TRANSIENT TABLE HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE (
        VACCINE VARCHAR(100) COMMENT 'Type of vaccine administered',
        GEOGRAPHY_TYPE VARCHAR(50) COMMENT 'Type of geographic region (e.g., States)',
        GEOGRAPHY VARCHAR(100) COMMENT 'Name of the geographic region',
        SEASON VARCHAR(20) COMMENT 'Vaccination season (e.g., 2018-19)',
        PERSONNEL_TYPE VARCHAR(100) COMMENT 'Category of healthcare personnel',
        ESTIMATE_PERCENTAGE FLOAT COMMENT 'Estimated vaccination coverage percentage',
        CONFIDENCE_INTERVAL_95_PERCENT VARCHAR(50) COMMENT '95% confidence interval for the estimate',
        SAMPLE_SIZE INTEGER COMMENT 'Number of individuals in the sample'
    )
    COMMENT = 'CDC Vaccination Coverage among Healthcare Personnel across different seasons and regions'
    """
    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    cursor.close()

def load_data(conn: snowflake.connector.SnowflakeConnection, file_path: str) -> None:
    """Load data from CSV into Snowflake table."""
    df = pd.read_csv(file_path)
    
    # Clean the data
    df['ESTIMATE (%)'] = pd.to_numeric(df['Estimate (%)'], errors='coerce')
    df['SAMPLE SIZE'] = pd.to_numeric(df['Sample Size'], errors='coerce')
    
    # Rename columns to match table structure
    df_renamed = df.rename(columns={
        'Vaccine': 'VACCINE',
        'Geography Type': 'GEOGRAPHY_TYPE',
        'Geography': 'GEOGRAPHY',
        'Season': 'SEASON',
        'Personnel Type': 'PERSONNEL_TYPE',
        'Estimate (%)': 'ESTIMATE_PERCENTAGE',
        '95% CI (%)': 'CONFIDENCE_INTERVAL_95_PERCENT',
        'Sample Size': 'SAMPLE_SIZE'
    })

    # Create temporary CSV for loading
    temp_csv = '/tmp/healthcare_personnel_temp.csv'
    df_renamed.to_csv(temp_csv, index=False, encoding='utf-8')

    # Load data into Snowflake
    cursor = conn.cursor()
    cursor.execute("PUT file://" + temp_csv + " @%HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE")
    cursor.execute("""
        COPY INTO HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE 
        FROM @%HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE 
        FILE_FORMAT = (
            TYPE = CSV 
            SKIP_HEADER = 1
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
        )
    """)
    cursor.close()

    # Clean up temporary file
    os.remove(temp_csv)

def main():
    conn = create_snowflake_connection()
    try:
        create_table(conn)
        load_data(conn, '/tmp/Vaccination_Coverage_among_Health_Care_Personnel.csv')
        print("Data loaded successfully!")
    finally:
        conn.close()

if __name__ == "__main__":
    main()