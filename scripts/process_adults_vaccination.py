import pandas as pd
import os
import snowflake.connector
from urllib.request import urlretrieve

# URLs for the datasets
META_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Adults_18_Years-meta.csv"
DATA_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Adults_18_Years.csv"

# Local paths
META_PATH = "/workspace/data/adults_vaccination_meta.csv"
DATA_PATH = "/workspace/data/adults_vaccination_data.csv"

# Download files
def download_files():
    os.makedirs("/workspace/data", exist_ok=True)
    urlretrieve(META_URL, META_PATH)
    urlretrieve(DATA_URL, DATA_PATH)

# Process metadata
def process_metadata():
    meta_df = pd.read_csv(META_PATH)
    return meta_df

# Process data and create table
def process_data():
    # Read the first 100 rows to analyze structure
    df = pd.read_csv(DATA_PATH, nrows=100)
    print("Data Preview:")
    print(df.head())
    print("\nColumns:", df.columns.tolist())
    return df

# Create Snowflake connection
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
    print("Downloading files...")
    download_files()
    
    print("\nProcessing metadata...")
    meta_df = process_metadata()
    print(meta_df)
    
    print("\nProcessing data...")
    data_df = process_data()

if __name__ == "__main__":
    main()