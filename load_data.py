import os
import sys
import logging
import snowflake.connector
from snowflake.connector.errors import ProgrammingError
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Snowflake connection parameters from environment variables
SNOWFLAKE_CONFIG = {
    'user': os.environ['SNOWFLAKE_USER'],
    'password': os.environ['SNOWFLAKE_PASSWORD'],
    'account': os.environ['SNOWFLAKE_ACCOUNT'],
    'warehouse': os.environ['SNOWFLAKE_WAREHOUSE'],
    'database': os.environ['SNOWFLAKE_DATABASE'],
    'schema': os.environ['SNOWFLAKE_SCHEMA'],
    'role': os.environ['SNOWFLAKE_ROLE']
}

# Mapping of CSV files to table names
TABLE_MAPPING = {
    'sub.csv': 'SUBMISSIONS',
    'num.csv': 'NUMBERS',
    'pre.csv': 'PRESENTATIONS',
    'tag.csv': 'TAGS'
}

def create_stage(conn) -> None:
    """Create an internal stage for file uploading if it doesn't exist."""
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE STAGE IF NOT EXISTS sec_filing_stage")
        logger.info("Stage created or already exists")
    except ProgrammingError as e:
        logger.error(f"Error creating stage: {e}")
        raise

def upload_to_stage(conn, file_path: str, file_name: str) -> None:
    """Upload a file to the Snowflake internal stage."""
    try:
        cursor = conn.cursor()
        put_command = f"PUT file://{file_path} @sec_filing_stage/{file_name} AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
        cursor.execute(put_command)
        logger.info(f"Successfully uploaded {file_name} to stage")
    except ProgrammingError as e:
        logger.error(f"Error uploading file to stage: {e}")
        raise

def copy_into_table(conn, table_name: str, file_name: str) -> None:
    """Copy staged file into the target table."""
    try:
        cursor = conn.cursor()
        copy_command = f"""
        COPY INTO {table_name}
        FROM @sec_filing_stage/{file_name}
        FILE_FORMAT = (
            TYPE = CSV
            FIELD_DELIMITER = ','
            SKIP_HEADER = 1
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            NULL_IF = ('', 'NULL', 'null')
            EMPTY_FIELD_AS_NULL = TRUE
            ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
        )
        ON_ERROR = 'CONTINUE'
        """
        cursor.execute(copy_command)
        logger.info(f"Successfully loaded data into {table_name}")
    except ProgrammingError as e:
        logger.error(f"Error copying data into table: {e}")
        raise

def main():
    """Main function to load data into Snowflake tables."""
    processed_dir = "/tmp/2024q4_processed"
    
    if not os.path.exists(processed_dir):
        logger.error(f"Processed directory {processed_dir} does not exist")
        sys.exit(1)

    try:
        # Establish Snowflake connection
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        logger.info("Connected to Snowflake successfully")

        # Create stage
        create_stage(conn)

        # Process each file
        for csv_file, table_name in TABLE_MAPPING.items():
            file_path = os.path.join(processed_dir, csv_file)
            if not os.path.exists(file_path):
                logger.error(f"File {file_path} does not exist")
                continue

            logger.info(f"Processing {csv_file} for table {table_name}")
            
            # Upload to stage
            upload_to_stage(conn, file_path, csv_file)
            
            # Copy into table
            copy_into_table(conn, table_name, csv_file)

        logger.info("Data loading completed successfully")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Snowflake connection closed")

if __name__ == "__main__":
    main()