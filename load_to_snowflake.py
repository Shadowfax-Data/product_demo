#!/usr/bin/env python3

import os
import sys
import csv
import logging
from datetime import datetime
import snowflake.connector
from snowflake.connector.errors import ProgrammingError
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Snowflake connection parameters
SNOWFLAKE_CONFIG = {
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'warehouse': 'COMPUTE_WH',
    'database': 'SHADOWFAX',
    'schema': 'DEV',
    'role': 'SHADOWFAX'
}

def create_snowflake_connection():
    """Create and return a Snowflake connection."""
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        logger.info("Successfully connected to Snowflake")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Snowflake: {str(e)}")
        raise

def load_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """Load data from CSV file into a list of dictionaries."""
    data = []
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Combine class and type fields for egg_type
                egg_type = row['class']
                if row['type'] and row['type'] != 'N/A':
                    egg_type = f"{egg_type} - {row['type']}"
                
                # Clean up volume and percent change
                volume = row['volume'] if row['volume'] != 'N/A' else None
                pct_change = row['pct_chg_last_week'].rstrip('%') if row['pct_chg_last_week'] != 'N/A' else None
                
                processed_row = {
                    'report_date': row['report_date'],
                    'region': None if row['region'] == 'N/A' else row['region'],
                    'egg_type': egg_type,
                    'volume_30doz_cases_thousands': volume,
                    'percent_change_last_week': pct_change
                }
                data.append(processed_row)
        logger.info(f"Successfully loaded {len(data)} rows from CSV")
        return data
    except Exception as e:
        logger.error(f"Failed to load CSV data: {str(e)}")
        raise

def batch_insert_data(conn, data: List[Dict[str, Any]], batch_size: int = 1000):
    """Insert data into Snowflake in batches."""
    cursor = conn.cursor()
    total_rows = len(data)
    inserted_rows = 0
    
    try:
        for i in range(0, total_rows, batch_size):
            batch = data[i:i + batch_size]
            values = []
            for row in batch:
                values.append((
                    row['report_date'],
                    row['region'],
                    row['egg_type'],
                    float(row['volume_30doz_cases_thousands']) if row['volume_30doz_cases_thousands'] else None,
                    float(row['percent_change_last_week']) if row['percent_change_last_week'] else None
                ))
            
            # Prepare the SQL statement
            insert_sql = """
                INSERT INTO usda_weekly_egg_inventory (
                    report_date,
                    region,
                    egg_type,
                    volume_30doz_cases_thousands,
                    percent_change_last_week
                )
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_sql, values)
            inserted_rows += len(batch)
            logger.info(f"Inserted batch of {len(batch)} rows. Progress: {inserted_rows}/{total_rows}")
            
        conn.commit()
        logger.info(f"Successfully inserted all {total_rows} rows into Snowflake")
    except Exception as e:
        logger.error(f"Error during batch insert: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def verify_data_load(conn):
    """Verify the data was loaded correctly."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM usda_weekly_egg_inventory")
        count = cursor.fetchone()[0]
        logger.info(f"Total rows in table: {count}")
        
        cursor.execute("""
            SELECT region, egg_type, COUNT(*)
            FROM usda_weekly_egg_inventory
            GROUP BY region, egg_type
            ORDER BY region, egg_type
        """)
        logger.info("\nData distribution by region and egg type:")
        for row in cursor:
            logger.info(f"{row[0]} - {row[1]}: {row[2]} records")
            
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        raise
    finally:
        cursor.close()

def main():
    if len(sys.argv) != 2:
        logger.error("Usage: python load_to_snowflake.py <csv_file_path>")
        sys.exit(1)
        
    csv_file_path = sys.argv[1]
    
    try:
        # Load CSV data
        data = load_csv_data(csv_file_path)
        
        # Connect to Snowflake
        conn = create_snowflake_connection()
        
        try:
            # Insert data in batches
            batch_insert_data(conn, data)
            
            # Verify the data load
            verify_data_load(conn)
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to complete data loading: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()