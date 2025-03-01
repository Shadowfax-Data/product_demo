import os
import argparse
from snowflake.connector import connect
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

def get_snowflake_connection():
    # Create a temporary file to store the private key
    private_key_path = '/tmp/snowflake_private_key.p8'
    private_key = os.environ['SNOWFLAKE_PRIVATE_KEY'].replace('\\n', '\n')
    with open(private_key_path, 'w') as f:
        f.write(private_key)

    with open(private_key_path, "rb") as key:
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

    # Remove the temporary private key file
    os.remove(private_key_path)

    conn = connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'],
        database=os.environ['SNOWFLAKE_DATABASE'],
        schema=os.environ['SNOWFLAKE_SCHEMA'],
        role=os.environ['SNOWFLAKE_ROLE'],
        warehouse='COMPUTE_WH',
        private_key=pkb
    )
    return conn

def create_tables(conn):
    cursor = conn.cursor()
    
    # Create SUB (Submission) table
    cursor.execute("""
    CREATE OR REPLACE TABLE SEC_SUBMISSIONS (
        adsh VARCHAR(20),
        cik INT,
        name VARCHAR(150),
        sic INT,
        countryba VARCHAR(2),
        stprba VARCHAR(2),
        cityba VARCHAR(30),
        zipba VARCHAR(10),
        bas1 VARCHAR(40),
        bas2 VARCHAR(40),
        baph VARCHAR(20),
        countryma VARCHAR(2),
        stprma VARCHAR(2),
        cityma VARCHAR(30),
        zipma VARCHAR(10),
        mas1 VARCHAR(40),
        mas2 VARCHAR(40),
        countryinc VARCHAR(2),
        stprinc VARCHAR(2),
        ein VARCHAR(10),
        former VARCHAR(150),
        changed VARCHAR(8),
        afs VARCHAR(5),
        wksi BOOLEAN,
        fye VARCHAR(4),
        form VARCHAR(10),
        period DATE,
        fy INT,
        fp VARCHAR(2),
        filed DATE,
        accepted TIMESTAMP,
        prevrpt BOOLEAN,
        detail BOOLEAN,
        instance VARCHAR(32),
        nciks INT,
        aciks VARCHAR(120),
        PRIMARY KEY (adsh)
    )
    """)

    # Create NUM (Numeric) table
    cursor.execute("""
    CREATE OR REPLACE TABLE SEC_NUMBERS (
        adsh VARCHAR(20),
        tag VARCHAR(256),
        version VARCHAR(20),
        coreg VARCHAR(256),
        ddate DATE,
        qtrs INT,
        uom VARCHAR(20),
        value FLOAT,
        footnote VARCHAR(512),
        FOREIGN KEY (adsh) REFERENCES SEC_SUBMISSIONS(adsh)
    )
    """)

    # Create TAG (Tags) table
    cursor.execute("""
    CREATE OR REPLACE TABLE SEC_TAGS (
        tag VARCHAR(256),
        version VARCHAR(20),
        custom BOOLEAN,
        abstract BOOLEAN,
        datatype VARCHAR(20),
        iord VARCHAR(1),
        crdr VARCHAR(1),
        tlabel VARCHAR(512),
        doc VARCHAR(8192)
    )
    """)

    # Create PRE (Presentation) table
    cursor.execute("""
    CREATE OR REPLACE TABLE SEC_PRESENTATIONS (
        adsh VARCHAR(20),
        report INT,
        line INT,
        stmt VARCHAR(2),
        inpth BOOLEAN,
        rfile VARCHAR(1),
        tag VARCHAR(256),
        version VARCHAR(20),
        plabel VARCHAR(512),
        FOREIGN KEY (adsh) REFERENCES SEC_SUBMISSIONS(adsh)
    )
    """)

    cursor.close()

def main():
    parser = argparse.ArgumentParser(description='Create Snowflake tables for SEC financial data')
    args = parser.parse_args()

    conn = get_snowflake_connection()
    try:
        create_tables(conn)
        print("Successfully created all tables in Snowflake")
    finally:
        conn.close()

if __name__ == '__main__':
    main()