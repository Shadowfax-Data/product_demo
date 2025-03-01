import os
import argparse
import csv
import snowflake.connector
from snowflake.connector.errors import ProgrammingError
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_snowflake_connection():
    """Establish connection to Snowflake using environment variables."""
    try:
        conn = snowflake.connector.connect(
            user=os.environ['SNOWFLAKE_USER'],
            password=os.environ['SNOWFLAKE_PASSWORD'],
            account=os.environ['SNOWFLAKE_ACCOUNT'],
            warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
            database=os.environ['SNOWFLAKE_DATABASE'],
            schema=os.environ['SNOWFLAKE_SCHEMA'],
            role=os.environ['SNOWFLAKE_ROLE']
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Snowflake: {str(e)}")
        raise

def load_data_to_snowflake(conn, csv_dir: str) -> Dict[str, int]:
    """
    Load CSV files into corresponding Snowflake tables.
    Returns a dictionary with table names and their row counts.
    """
    file_table_mapping = {
        'num.csv': 'SEC_NUMERICAL_DATA',
        'pre.csv': 'SEC_PRESENTATION',
        'sub.csv': 'SEC_SUBMISSIONS',
        'tag.csv': 'SEC_TAGS'
    }
    
    row_counts = {}
    
    for csv_file, table_name in file_table_mapping.items():
        file_path = os.path.join(csv_dir, csv_file)
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            continue
            
        try:
            logger.info(f"Loading data from {csv_file} into {table_name}")
            
            # Read CSV file with more robust error handling
            df = pd.read_csv(
                file_path,
                low_memory=False,
                on_bad_lines='skip',  # Skip problematic lines
                quoting=csv.QUOTE_MINIMAL,
                encoding='utf-8'
            )
            
            # Handle date format conversions for submissions table
            if table_name == 'SEC_SUBMISSIONS':
                if 'changed' in df.columns:
                    df['changed'] = pd.to_datetime(df['changed']).dt.strftime('%Y%m%d').astype(float)
                if 'filed' in df.columns:
                    df['filed'] = pd.to_datetime(df['filed']).dt.strftime('%Y%m%d').astype(float)
                if 'accepted' in df.columns:
                    df['accepted'] = pd.to_datetime(df['accepted']).dt.strftime('%Y%m%d%H%M%S').astype(float)
            
            # Convert column names to uppercase for Snowflake
            df.columns = [col.upper() for col in df.columns]
            
            # Create temporary stage for bulk loading
            stage_name = f"TEMP_STAGE_{table_name}"
            cursor = conn.cursor()
            
            cursor.execute(f"CREATE OR REPLACE TEMPORARY STAGE {stage_name}")
            
            # Use write_pandas for efficient bulk loading
            success, nchunks, nrows, _ = write_pandas(
                conn=conn,
                df=df,
                table_name=table_name,
                quote_identifiers=False
            )
            
            if success:
                logger.info(f"Successfully loaded {nrows} rows into {table_name}")
                row_counts[table_name] = nrows
            else:
                logger.error(f"Failed to load data into {table_name}")
                
            # Cleanup
            cursor.execute(f"DROP STAGE IF EXISTS {stage_name}")
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error loading {csv_file} into {table_name}: {str(e)}")
            raise

    return row_counts

def main():
    parser = argparse.ArgumentParser(description='Load SEC data into Snowflake tables')
    parser.add_argument('--csv_dir', required=True, help='Directory containing the CSV files')
    args = parser.parse_args()
    
    try:
        conn = get_snowflake_connection()
        logger.info("Connected to Snowflake successfully")
        
        row_counts = load_data_to_snowflake(conn, args.csv_dir)
        
        logger.info("Data loading summary:")
        for table, count in row_counts.items():
            logger.info(f"{table}: {count} rows")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Snowflake connection closed")

if __name__ == "__main__":
    main()