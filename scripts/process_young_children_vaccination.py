import pandas as pd
import os
import requests
from snowflake.connector.pandas_tools import write_pandas
import snowflake.connector
import numpy as np

# Snowflake connection parameters from environment variables
SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'database': 'CDC_DATASET',
    'schema': 'PUBLIC',
    'role': os.getenv('SNOWFLAKE_ROLE')
}

# URLs for the datasets
META_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Young_Children_0-35_Months-meta.csv"
DATA_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Young_Children_0-35_Months.csv"

def download_file(url, local_filename):
    """Download a file from URL to local path"""
    if not os.path.exists('data'):
        os.makedirs('data')
    local_path = os.path.join('data', local_filename)
    response = requests.get(url)
    with open(local_path, 'wb') as f:
        f.write(response.content)
    return local_path

def clean_column_name(name):
    """Clean column name to make it Snowflake-friendly"""
    return name.upper().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('%', 'PCT').replace('+', 'PLUS')

def process_data():
    # Download files
    meta_file = download_file(META_URL, 'young_children_meta.csv')
    data_file = download_file(DATA_URL, 'young_children_data.csv')

    # Read metadata for column descriptions
    meta_df = pd.read_csv(meta_file)
    print("Metadata columns:", meta_df.columns.tolist())
    
    # Read the actual data
    df = pd.read_csv(data_file)
    print("Data columns:", df.columns.tolist())
    
    # Map columns to match Snowflake schema
    column_mapping = {
        'Vaccine': 'VACCINE',
        'Dose': 'DOSE',
        'Geography Type': 'GEOGRAPHY_TYPE',
        'Geography': 'GEOGRAPHY',
        'Birth Year/Birth Cohort': 'BIRTH_YEAR_COHORT',
        'Dimension Type': 'DIMENSION_TYPE',
        'Dimension': 'DIMENSION',
        'Estimate (%)': 'ESTIMATE_PCT',
        '95% CI (%)': 'CI_95_PCT',
        'Sample Size': 'SAMPLE_SIZE'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Replace special values with NULL
    df = df.replace(['NR*', 'NR', '--'], np.nan)
    
    # Convert numeric columns
    df['ESTIMATE_PCT'] = pd.to_numeric(df['ESTIMATE_PCT'], errors='coerce')
    df['SAMPLE_SIZE'] = pd.to_numeric(df['SAMPLE_SIZE'], errors='coerce')

    # Create Snowflake table
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()

    # Create table
    create_table_sql = """
    CREATE OR REPLACE TABLE YOUNG_CHILDREN_VACCINATION_COVERAGE (
        VACCINE VARCHAR(100),
        DOSE VARCHAR(100),
        GEOGRAPHY_TYPE VARCHAR(100),
        GEOGRAPHY VARCHAR(100),
        BIRTH_YEAR_COHORT VARCHAR(100),
        DIMENSION_TYPE VARCHAR(100),
        DIMENSION VARCHAR(100),
        ESTIMATE_PCT FLOAT,
        CI_95_PCT VARCHAR(100),
        SAMPLE_SIZE NUMBER
    )
    """
    cursor.execute(create_table_sql)

    # Add table comment
    cursor.execute("COMMENT ON TABLE YOUNG_CHILDREN_VACCINATION_COVERAGE IS 'Vaccination coverage data for children aged 0-35 months across different vaccines, locations, and demographic dimensions'")
    
    # Add column comments
    comments = [
        ("VACCINE", "Type of vaccine administered"),
        ("DOSE", "Dose number or schedule of the vaccine"),
        ("GEOGRAPHY_TYPE", "Type of geographic region (National, State, etc.)"),
        ("GEOGRAPHY", "Specific geographic location"),
        ("BIRTH_YEAR_COHORT", "Birth year or cohort of the children"),
        ("DIMENSION_TYPE", "Type of demographic dimension being measured"),
        ("DIMENSION", "Specific demographic category"),
        ("ESTIMATE_PCT", "Estimated vaccination coverage percentage"),
        ("CI_95_PCT", "95% confidence interval percentage range"),
        ("SAMPLE_SIZE", "Number of children in the sample")
    ]
    
    for col, comment in comments:
        cursor.execute(f"COMMENT ON COLUMN YOUNG_CHILDREN_VACCINATION_COVERAGE.{col} IS '{comment}'")
    
    # Load data into Snowflake
    success, nchunks, nrows, _ = write_pandas(
        conn=conn,
        df=df,
        table_name='YOUNG_CHILDREN_VACCINATION_COVERAGE',
        database='CDC_DATASET',
        schema='PUBLIC'
    )
    
    print(f"Data loaded successfully: {success}")
    print(f"Number of chunks: {nchunks}")
    print(f"Number of rows: {nrows}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    process_data()