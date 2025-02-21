import os
import pandas as pd
import snowflake.connector
from typing import Dict, List, Tuple
import urllib.request
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def download_csv(url: str, local_path: str) -> None:
    """Download a CSV file from a URL to a local path."""
    logger.info(f"Downloading {url} to {local_path}")
    urllib.request.urlretrieve(url, local_path)

def read_metadata(meta_csv_path: str) -> Dict:
    """Read and process the metadata CSV file."""
    logger.info(f"Reading metadata from {meta_csv_path}")
    meta_df = pd.read_csv(meta_csv_path)
    return meta_df.to_dict('records')

def read_data_sample(data_csv_path: str, nrows: int = 100) -> pd.DataFrame:
    """Read a sample of rows from the data CSV file."""
    logger.info(f"Reading {nrows} rows from {data_csv_path}")
    return pd.read_csv(data_csv_path, nrows=nrows)

def create_snowflake_table(conn, table_name: str, column_definitions: List[str], 
                          table_comment: str, column_comments: Dict[str, str]) -> None:
    """Create a table in Snowflake with comments."""
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {', '.join(column_definitions)}
    )
    COMMENT = '{table_comment}'
    """
    
    with conn.cursor() as cursor:
        cursor.execute(create_table_sql)
        
        # Add column comments
        for col, comment in column_comments.items():
            cursor.execute(f"COMMENT ON COLUMN {table_name}.{col} IS '{comment}'")

def load_data_to_snowflake(conn, table_name: str, data_csv_path: str) -> None:
    """Load CSV data into Snowflake table."""
    logger.info(f"Loading data from {data_csv_path} into {table_name}")
    
    # Read CSV in chunks and load to Snowflake
    chunk_size = 10000
    for chunk in pd.read_csv(data_csv_path, chunksize=chunk_size):
        # Clean column names
        chunk.columns = [col.strip().upper().replace(' ', '_') for col in chunk.columns]
        
        # Convert DataFrame to list of tuples
        values = [tuple(x) for x in chunk.values]
        
        # Generate the placeholders for the INSERT statement
        placeholders = ','.join(['%s'] * len(chunk.columns))
        
        # Execute the INSERT
        with conn.cursor() as cursor:
            cursor.executemany(
                f"INSERT INTO {table_name} VALUES ({placeholders})",
                values
            )

def get_snowflake_connection():
    """Create and return a Snowflake connection."""
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

def create_markdown_doc(table_name: str, metadata: Dict, sample_queries: List[str], 
                       output_path: str) -> None:
    """Create markdown documentation for a table."""
    with open(output_path, 'w') as f:
        f.write(f"# {table_name}\n\n")
        f.write("## Description\n")
        f.write(f"{metadata.get('description', 'No description available')}\n\n")
        
        f.write("## Columns\n")
        f.write("| Column Name | Description | Type |\n")
        f.write("|------------|-------------|------|\n")
        for col in metadata.get('columns', []):
            f.write(f"| {col['name']} | {col['description']} | {col['type']} |\n")
        
        f.write("\n## Sample Queries\n")
        for query in sample_queries:
            f.write(f"```sql\n{query}\n```\n\n")

def process_dataset(meta_url: str, data_url: str, table_name: str) -> None:
    """Process a single CDC dataset end-to-end."""
    # Create local paths
    meta_file = f"/workspace/data/{table_name}_meta.csv"
    data_file = f"/workspace/data/{table_name}.csv"
    doc_file = f"/workspace/docs/{table_name}.md"
    
    # Download files
    download_csv(meta_url, meta_file)
    download_csv(data_url, data_file)
    
    # Process metadata and create table
    metadata = read_metadata(meta_file)
    data_sample = read_data_sample(data_file)
    
    # Connect to Snowflake and process
    with get_snowflake_connection() as conn:
        # Implementation details will vary based on specific dataset
        pass  # Placeholder for dataset-specific implementation