#!/usr/bin/env python3

import os
import sys
import csv
import logging
import argparse
from typing import List
import snowflake.connector
from snowflake.connector.errors import ProgrammingError, DatabaseError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_snowflake_connection():
    """Create and return a Snowflake connection using environment variables."""
    try:
        return snowflake.connector.connect(
            account=os.environ['SNOWFLAKE_ACCOUNT'],
            user=os.environ['SNOWFLAKE_USER'],
            password=os.environ['SNOWFLAKE_PASSWORD'],
            warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
            database=os.environ['SNOWFLAKE_DATABASE'],
            schema=os.environ['SNOWFLAKE_SCHEMA'],
            role=os.environ['SNOWFLAKE_ROLE']
        )
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to connect to Snowflake: {e}")
        sys.exit(1)

def load_csv_to_snowflake(conn, csv_file: str) -> None:
    """Load CSV data into Snowflake table."""
    try:
        cursor = conn.cursor()
        
        # First, truncate the table to ensure clean data load
        logger.info("Truncating existing table...")
        cursor.execute("TRUNCATE TABLE shadowfax.public.usda_weekly_egg_inventory")
        
        # Read CSV file and prepare for bulk insert
        with open(csv_file, 'r') as f:
            csv_reader = csv.DictReader(f)
            batch_size = 1000
            batch: List[tuple] = []
            
            insert_sql = """
            INSERT INTO shadowfax.public.usda_weekly_egg_inventory (
                report_date, region, type, class, package, volume, pct_chg_last_week
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            total_rows = 0
            for row in csv_reader:
                record = (
                    row['report_date'],
                    row['region'],
                    row['type'],
                    row['class'],
                    row['package'],
                    row['volume'],
                    row['pct_chg_last_week']
                )
                batch.append(record)
                
                if len(batch) >= batch_size:
                    cursor.executemany(insert_sql, batch)
                    total_rows += len(batch)
                    logger.info(f"Loaded {total_rows} rows...")
                    batch = []
            
            # Insert any remaining records
            if batch:
                cursor.executemany(insert_sql, batch)
                total_rows += len(batch)
            
            logger.info(f"Successfully loaded {total_rows} total rows into Snowflake")
            
    except (ProgrammingError, DatabaseError) as e:
        logger.error(f"Snowflake error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def main():
    parser = argparse.ArgumentParser(description='Load USDA egg inventory data into Snowflake')
    parser.add_argument('csv_file', help='Path to the CSV file to load')
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        logger.error(f"CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    conn = get_snowflake_connection()
    try:
        load_csv_to_snowflake(conn, args.csv_file)
        logger.info("Data loading completed successfully")
    finally:
        conn.close()

if __name__ == '__main__':
    main()