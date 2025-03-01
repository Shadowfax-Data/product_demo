import os
import snowflake.connector
from typing import Dict, Any

def get_snowflake_connection():
    """Establish connection to Snowflake using environment variables."""
    return snowflake.connector.connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'],
        password=os.environ['SNOWFLAKE_PASSWORD'],
        warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
        database=os.environ['SNOWFLAKE_DATABASE'],
        schema=os.environ['SNOWFLAKE_SCHEMA'],
        role=os.environ['SNOWFLAKE_ROLE']
    )

def execute_query(conn, query: str) -> None:
    """Execute a query and handle any errors."""
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        cursor.close()
    except Exception as e:
        print(f"Error executing query: {e}")
        raise

def create_tables(conn) -> None:
    """Create the SEC financial statement tables in Snowflake."""
    
    # Create SUBMISSIONS table
    submissions_table = """
    CREATE OR REPLACE TABLE SUBMISSIONS (
        adsh VARCHAR(20) NOT NULL COMMENT 'EDGAR Accession Number - Primary Key',
        cik INT COMMENT 'Central Index Key (CIK)',
        name VARCHAR(150) COMMENT 'Company Name',
        sic INT COMMENT 'Standard Industrial Classification (SIC)',
        countryba VARCHAR(2) COMMENT 'Business Address Country',
        stprba VARCHAR(2) COMMENT 'Business Address State/Province',
        cityba VARCHAR(30) COMMENT 'Business Address City',
        zipba VARCHAR(10) COMMENT 'Business Address Zip',
        bas1 VARCHAR(40) COMMENT 'Business Address Street 1',
        bas2 VARCHAR(40) COMMENT 'Business Address Street 2',
        baph VARCHAR(20) COMMENT 'Business Address Phone',
        countryma VARCHAR(2) COMMENT 'Mailing Address Country',
        stprma VARCHAR(2) COMMENT 'Mailing Address State/Province',
        cityma VARCHAR(30) COMMENT 'Mailing Address City',
        zipma VARCHAR(10) COMMENT 'Mailing Address Zip',
        mas1 VARCHAR(40) COMMENT 'Mailing Address Street 1',
        mas2 VARCHAR(40) COMMENT 'Mailing Address Street 2',
        countryinc VARCHAR(3) COMMENT 'Country of Incorporation',
        stprinc VARCHAR(2) COMMENT 'State of Incorporation',
        ein VARCHAR(10) COMMENT 'Employee Identification Number',
        former VARCHAR(150) COMMENT 'Former Name',
        changed VARCHAR(8) COMMENT 'Date of Name Change (YYYYMMDD)',
        afs VARCHAR(5) COMMENT 'Filer Status',
        wksi BOOLEAN COMMENT 'Well-Known Seasoned Issuer',
        fye VARCHAR(4) COMMENT 'Fiscal Year End (MMDD)',
        form VARCHAR(10) COMMENT 'SEC Form Type',
        period DATE COMMENT 'Period End Date',
        fy INT COMMENT 'Fiscal Year',
        fp VARCHAR(2) COMMENT 'Fiscal Period',
        filed DATE COMMENT 'Filing Date',
        accepted TIMESTAMP_NTZ COMMENT 'Accepted Timestamp',
        prevrpt BOOLEAN COMMENT 'Previous Report',
        detail BOOLEAN COMMENT 'Detail Flag',
        instance VARCHAR(32) COMMENT 'Instance Document File Name',
        nciks INT COMMENT 'Number of CIKs',
        aciks VARCHAR(120) COMMENT 'Additional CIKs',
        PRIMARY KEY (adsh)
    ) COMMENT = 'SEC EDGAR Submission Information and Company Details';
    """
    
    # Create NUMBERS table
    numbers_table = """
    CREATE OR REPLACE TABLE NUMBERS (
        adsh VARCHAR(20) NOT NULL COMMENT 'EDGAR Accession Number - Foreign Key to SUBMISSIONS',
        tag VARCHAR(256) NOT NULL COMMENT 'XBRL Tag - Foreign Key to TAGS',
        version VARCHAR(20) COMMENT 'XBRL Version',
        coreg VARCHAR(256) COMMENT 'Co-registrant CIK',
        ddate DATE NOT NULL COMMENT 'Data Date',
        qtrs INT COMMENT 'Number of Quarters',
        uom VARCHAR(20) COMMENT 'Unit of Measure',
        value FLOAT COMMENT 'Value',
        footnote VARCHAR(512) COMMENT 'Footnote',
        PRIMARY KEY (adsh, tag, ddate)
    ) COMMENT = 'Financial Statement Numeric Data Points';
    """
    
    # Create PRESENTATIONS table
    presentations_table = """
    CREATE OR REPLACE TABLE PRESENTATIONS (
        adsh VARCHAR(20) NOT NULL COMMENT 'EDGAR Accession Number - Foreign Key to SUBMISSIONS',
        report INT NOT NULL COMMENT 'Report Index',
        line INT NOT NULL COMMENT 'Line Index',
        stmt VARCHAR(2) COMMENT 'Financial Statement Type (IS=Income, BS=Balance Sheet, CF=Cash Flow, EQ=Equity, CI=Comprehensive Income)',
        inpth BOOLEAN COMMENT 'Parent-Child Relationship Indicator',
        rfile VARCHAR(1) COMMENT 'Reference File Type',
        tag VARCHAR(256) COMMENT 'XBRL Tag - Foreign Key to TAGS',
        version VARCHAR(20) COMMENT 'XBRL Version',
        plabel VARCHAR(512) COMMENT 'Preferred Label',
        negating BOOLEAN COMMENT 'Negating Label Indicator',
        PRIMARY KEY (adsh, report, line)
    ) COMMENT = 'Financial Statement Presentation and Structure Information';
    """
    
    # Create TAGS table
    tags_table = """
    CREATE OR REPLACE TABLE TAGS (
        tag VARCHAR(256) NOT NULL COMMENT 'XBRL Tag Name',
        version VARCHAR(20) NOT NULL COMMENT 'XBRL Version',
        custom BOOLEAN COMMENT 'Custom Tag Indicator',
        abstract BOOLEAN COMMENT 'Abstract Element Indicator',
        datatype VARCHAR(20) COMMENT 'Data Type',
        iord VARCHAR(1) COMMENT 'Item or Dimension (I=Item, D=Dimension)',
        crdr VARCHAR(1) COMMENT 'Credit/Debit (C=Credit, D=Debit)',
        tlabel VARCHAR(512) COMMENT 'Tag Label',
        doc VARCHAR(8192) COMMENT 'Documentation',
        PRIMARY KEY (tag, version)
    ) COMMENT = 'XBRL Tags and Definitions Reference';
    """
    
    # Execute table creation queries
    tables = [submissions_table, numbers_table, presentations_table, tags_table]
    
    for table_query in tables:
        execute_query(conn, table_query)
        print(f"Successfully created table from query: {table_query.split('CREATE OR REPLACE TABLE')[1].split('(')[0].strip()}")

def main():
    """Main function to create Snowflake tables."""
    print("Establishing connection to Snowflake...")
    conn = get_snowflake_connection()
    
    try:
        print("Creating tables...")
        create_tables(conn)
        print("Successfully created all tables!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()