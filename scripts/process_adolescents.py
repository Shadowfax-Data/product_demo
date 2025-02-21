import pandas as pd
import os
import requests
from snowflake.connector.pandas_tools import write_pandas
import snowflake.connector
import tempfile

# URLs for the datasets
META_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Adolescents_13-17_Years-meta.csv"
DATA_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Adolescents_13-17_Years.csv"

def download_file(url, local_path):
    response = requests.get(url)
    response.raise_for_status()
    with open(local_path, 'wb') as f:
        f.write(response.content)

def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'],
        password=os.environ['SNOWFLAKE_PASSWORD'],
        warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
        database='CDC_DATASET',
        schema='PUBLIC',
        role=os.environ['SNOWFLAKE_ROLE']
    )

def main():
    # Create data directory if it doesn't exist
    os.makedirs('/workspace/data', exist_ok=True)
    
    # Download files
    meta_path = '/workspace/data/adolescents_meta.csv'
    data_path = '/workspace/data/adolescents_data.csv'
    
    print("Downloading metadata file...")
    download_file(META_URL, meta_path)
    print("Downloading data file...")
    download_file(DATA_URL, data_path)
    
    # Read metadata
    meta_df = pd.read_csv(meta_path)
    print("\nMetadata Preview:")
    print(meta_df.head())
    
    # Read data
    data_df = pd.read_csv(data_path)
    print("\nData Preview:")
    print(data_df.head())
    
    # Connect to Snowflake
    conn = get_snowflake_connection()
    
    # Create table
    create_table_sql = """
    CREATE OR REPLACE TABLE ADOLESCENT_VACCINATION_COVERAGE (
        YEAR NUMBER(4) COMMENT 'Year of data collection',
        LOCATION VARCHAR COMMENT 'Geographic location (state or territory)',
        AGE_GROUP VARCHAR COMMENT 'Age group of adolescents (13-17 years)',
        VACCINE_TYPE VARCHAR COMMENT 'Type of vaccine administered',
        COVERAGE_PCT FLOAT COMMENT 'Vaccination coverage percentage',
        SAMPLE_SIZE NUMBER COMMENT 'Number of adolescents in the sample',
        CONFIDENCE_INTERVAL_LOW FLOAT COMMENT 'Lower bound of 95% confidence interval',
        CONFIDENCE_INTERVAL_HIGH FLOAT COMMENT 'Upper bound of 95% confidence interval'
    ) COMMENT = 'CDC Vaccination Coverage among Adolescents aged 13-17 Years'
    """
    
    with conn.cursor() as cursor:
        cursor.execute(create_table_sql)
    
    # Clean and prepare data for loading
    # Rename columns to match Snowflake table
    data_df = data_df.rename(columns={
        'Survey Year': 'YEAR',
        'Geography': 'LOCATION',
        'Dimension': 'AGE_GROUP',
        'Vaccine/Sample': 'VACCINE_TYPE',
        'Estimate (%)': 'COVERAGE_PCT',
        'Sample Size': 'SAMPLE_SIZE',
    })
    
    # Extract confidence intervals
    data_df[['CONFIDENCE_INTERVAL_LOW', 'CONFIDENCE_INTERVAL_HIGH']] = data_df['95% CI (%)'].str.extract(r'([\d.]+) to ([\d.]+)')
    
    # Convert data types
    data_df['YEAR'] = pd.to_numeric(data_df['YEAR'], errors='coerce')
    data_df['COVERAGE_PCT'] = pd.to_numeric(data_df['COVERAGE_PCT'], errors='coerce')
    data_df['SAMPLE_SIZE'] = pd.to_numeric(data_df['SAMPLE_SIZE'], errors='coerce')
    data_df['CONFIDENCE_INTERVAL_LOW'] = pd.to_numeric(data_df['CONFIDENCE_INTERVAL_LOW'], errors='coerce')
    data_df['CONFIDENCE_INTERVAL_HIGH'] = pd.to_numeric(data_df['CONFIDENCE_INTERVAL_HIGH'], errors='coerce')
    
    # Select and reorder columns
    final_df = data_df[[
        'YEAR',
        'LOCATION',
        'AGE_GROUP',
        'VACCINE_TYPE',
        'COVERAGE_PCT',
        'SAMPLE_SIZE',
        'CONFIDENCE_INTERVAL_LOW',
        'CONFIDENCE_INTERVAL_HIGH'
    ]]
    
    # Replace NaN with None for Snowflake compatibility
    final_df = final_df.where(pd.notnull(final_df), None)
    
    # Load data into Snowflake
    print("\nLoading data into Snowflake...")
    success, nchunks, nrows, _ = write_pandas(
        conn=conn,
        df=final_df,
        table_name='ADOLESCENT_VACCINATION_COVERAGE',
        database='CDC_DATASET',
        schema='PUBLIC'
    )
    
    print(f"Data loaded successfully: {success}")
    print(f"Number of chunks: {nchunks}")
    print(f"Number of rows: {nrows}")
    
    conn.close()

if __name__ == "__main__":
    main()