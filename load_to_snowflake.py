import argparse
import os
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_snowflake_connection():
    with open(os.environ['SNOWFLAKE_PRIVATE_KEY'], 'rb') as key:
        p_key = serialization.load_pem_private_key(
            key.read(),
            password=None,
            backend=default_backend()
        )

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return snowflake.connector.connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'],
        database=os.environ['SNOWFLAKE_DATABASE'],
        schema=os.environ['SNOWFLAKE_SCHEMA'],
        role=os.environ['SNOWFLAKE_ROLE'],
        private_key=pkb
    )

def create_stage(cursor):
    cursor.execute("CREATE OR REPLACE STAGE sec_data_stage")
    logging.info("Created temporary stage: sec_data_stage")

def upload_to_stage(cursor, file_path, file_name):
    put_command = f"PUT file://{file_path} @sec_data_stage/{file_name} AUTO_COMPRESS=TRUE"
    cursor.execute(put_command)
    logging.info(f"Uploaded {file_name} to stage")

def load_table(cursor, table_name, file_name):
    copy_command = f"""
    COPY INTO {table_name}
    FROM @sec_data_stage/{file_name}
    FILE_FORMAT = (
        TYPE = CSV
        FIELD_DELIMITER = ','
        SKIP_HEADER = 1
        NULL_IF = ('', 'NULL', 'null')
        EMPTY_FIELD_AS_NULL = TRUE
    )
    ON_ERROR = CONTINUE;
    """
    cursor.execute(copy_command)
    logging.info(f"Loaded data into {table_name}")

def cleanup_stage(cursor):
    cursor.execute("DROP STAGE IF EXISTS sec_data_stage")
    logging.info("Cleaned up temporary stage")

def main():
    parser = argparse.ArgumentParser(description='Load SEC data into Snowflake tables')
    parser.add_argument('--input-dir', required=True, help='Directory containing CSV files')
    args = parser.parse_args()

    # File to table mapping
    file_mapping = {
        'sub.csv': 'SEC_SUBMISSIONS',
        'num.csv': 'SEC_NUMBERS',
        'tag.csv': 'SEC_TAGS',
        'pre.csv': 'SEC_PRESENTATIONS'
    }

    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Create temporary stage
        create_stage(cursor)

        # Process each file
        for csv_file, table_name in file_mapping.items():
            file_path = os.path.join(args.input_dir, csv_file)
            if not os.path.exists(file_path):
                logging.warning(f"File not found: {file_path}")
                continue

            logging.info(f"Processing {csv_file} for table {table_name}")
            upload_to_stage(cursor, file_path, csv_file)
            load_table(cursor, table_name, csv_file)

        # Cleanup
        cleanup_stage(cursor)
        logging.info("Data loading completed successfully")

    except Exception as e:
        logging.error(f"Error during data loading: {str(e)}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()