import pandas as pd
import os
import snowflake.connector
from urllib.request import urlretrieve
from snowflake.connector.pandas_tools import write_pandas

# Download URLs
META_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Health_Care_Personnel-meta.csv"
DATA_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Health_Care_Personnel.csv"

# Local file paths
META_FILE = "../data/healthcare_personnel_meta.csv"
DATA_FILE = "../data/healthcare_personnel_data.csv"

# Download files
def download_files():
    os.makedirs("../data", exist_ok=True)
    urlretrieve(META_URL, META_FILE)
    urlretrieve(DATA_URL, DATA_FILE)

# Read and analyze metadata
def analyze_metadata():
    meta_df = pd.read_csv(META_FILE)
    print("\nMetadata Analysis:")
    print(meta_df)
    return meta_df

# Read and analyze data
def analyze_data():
    data_df = pd.read_csv(DATA_FILE)
    
    # Clean up column names
    data_df.columns = [
        'VACCINE',
        'GEOGRAPHY_TYPE',
        'GEOGRAPHY',
        'SEASON',
        'PERSONNEL_TYPE',
        'ESTIMATE_PCT',
        'CONFIDENCE_INTERVAL_PCT',
        'SAMPLE_SIZE'
    ]
    
    print("\nData Analysis:")
    print(data_df.head())
    print("\nColumns:", data_df.columns.tolist())
    print("\nData Types:\n", data_df.dtypes)
    print("\nSample Records:\n", data_df.head())
    return data_df

# Load data to Snowflake
def load_to_snowflake(df):
    # Snowflake connection parameters from environment variables
    conn = snowflake.connector.connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'],
        password=os.environ['SNOWFLAKE_PASSWORD'],
        warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
        database='CDC_DATASET',
        schema='PUBLIC',
        role=os.environ['SNOWFLAKE_ROLE']
    )
    
    # Create table
    cursor = conn.cursor()
    
    create_table_sql = """
    CREATE OR REPLACE TABLE HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE (
        VACCINE VARCHAR COMMENT 'Type of vaccine administered',
        GEOGRAPHY_TYPE VARCHAR COMMENT 'Type of geographic region (e.g., States, National)',
        GEOGRAPHY VARCHAR COMMENT 'Name of the geographic location',
        SEASON VARCHAR COMMENT 'Vaccination season (e.g., 2020-21)',
        PERSONNEL_TYPE VARCHAR COMMENT 'Category of healthcare personnel',
        ESTIMATE_PCT FLOAT COMMENT 'Vaccination coverage estimate percentage',
        CONFIDENCE_INTERVAL_PCT FLOAT COMMENT '95% confidence interval percentage',
        SAMPLE_SIZE NUMBER COMMENT 'Number of healthcare personnel in the sample'
    ) COMMENT = 'Vaccination coverage data among healthcare personnel across different locations and seasons'
    """
    
    cursor.execute(create_table_sql)
    
    # Write the dataframe to Snowflake
    success, nchunks, nrows, _ = write_pandas(
        conn=conn,
        df=df,
        table_name='HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE',
        database='CDC_DATASET',
        schema='PUBLIC'
    )
    
    print(f"Data loaded successfully: {success}")
    print(f"Number of chunks: {nchunks}")
    print(f"Number of rows: {nrows}")
    
    conn.close()

def main():
    print("Downloading files...")
    download_files()
    
    print("Analyzing metadata...")
    meta_df = analyze_metadata()
    
    print("Analyzing data...")
    data_df = analyze_data()
    
    print("Loading data to Snowflake...")
    load_to_snowflake(data_df)

if __name__ == "__main__":
    main()