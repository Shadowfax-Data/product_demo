#!/usr/bin/env python3

import os
import sys
import csv
import logging
import argparse
from typing import List, Dict
import snowflake.connector
from snowflake.connector.errors import ProgrammingError
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_snowflake_connection():
    """Create and return a Snowflake connection."""
    try:
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT', 'iwuiwka-hcb25806'),
            user=os.getenv('SNOWFLAKE_USER', 'DIWU_SHADOWFAX_PASSWORD'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            warehouse='COMPUTE_WH',
            database='SHADOWFAX',
            schema='PUBLIC',
            role='SHADOWFAX'
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Snowflake: {str(e)}")
        raise

def load_data_to_snowflake(csv_path: str, batch_size: int = 10000):
    """
    Load data from CSV to Snowflake using batch processing.
    
    Args:
        csv_path: Path to the CSV file
        batch_size: Number of rows to process in each batch
    """
    try:
        # Read CSV file using pandas
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from CSV file")

        # Convert column names to uppercase
        df.columns = [col.upper() for col in df.columns]

        # Convert percentage strings to numbers
        df['PCT_CHG_LAST_WEEK'] = df['PCT_CHG_LAST_WEEK'].str.rstrip('%').astype('float')

        # Convert date string to date
        df['REPORT_DATE'] = pd.to_datetime(df['REPORT_DATE'], format='%m/%d/%Y').dt.strftime('%Y-%m-%d')

        # Add CREATED_AT column
        df['CREATED_AT'] = pd.Timestamp.now()

        # Connect to Snowflake
        conn = get_snowflake_connection()
        
        # Print DataFrame info for debugging
        logger.info("DataFrame info:")
        logger.info(df.dtypes)
        logger.info("\nSample data:")
        logger.info(df.head())

        # Convert DataFrame to SQL values
        values = []
        for _, row in df.iterrows():
            region = 'NULL' if pd.isna(row['REGION']) else f"'{row['REGION']}'"
            pct_chg = 'NULL' if pd.isna(row['PCT_CHG_LAST_WEEK']) else str(row['PCT_CHG_LAST_WEEK'])
            values.append(
                f"('{row['REPORT_DATE']}', {region}, '{row['EGG_CLASS']}', "
                f"{row['VOLUME']}, {pct_chg}, '{row['PACKAGE']}', "
                f"CURRENT_TIMESTAMP())"
            )

        # Insert data in batches
        batch_size = 1000
        for i in range(0, len(values), batch_size):
            batch = values[i:i + batch_size]
            insert_sql = f"""
                INSERT INTO SHADOWFAX.PUBLIC.USDA_WEEKLY_EGG_INVENTORY 
                (report_date, region, egg_class, volume, pct_chg_last_week, package, created_at)
                VALUES {','.join(batch)}
            """
            cursor = conn.cursor()
            cursor.execute(insert_sql)
            cursor.close()
            logger.info(f"Inserted batch {i//batch_size + 1} of {(len(values) + batch_size - 1)//batch_size}")

        nrows = len(values)
        nchunks = (len(values) + batch_size - 1) // batch_size
        
        logger.info(f"Successfully loaded {nrows} rows in {nchunks} chunks")
        
        # Verify row count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM SHADOWFAX.PUBLIC.USDA_WEEKLY_EGG_INVENTORY")
        count = cursor.fetchone()[0]
        logger.info(f"Total rows in Snowflake table: {count}")
        
        if count != len(df):
            logger.warning(f"Row count mismatch: CSV has {len(df)} rows, but Snowflake has {count} rows")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error loading data to Snowflake: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Load egg inventory data to Snowflake')
    parser.add_argument('csv_file', help='Path to the CSV file to load')
    parser.add_argument('--batch-size', type=int, default=10000,
                      help='Number of rows to process in each batch')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        logger.error(f"CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    try:
        load_data_to_snowflake(args.csv_file, args.batch_size)
        logger.info("Data loading completed successfully")
    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()