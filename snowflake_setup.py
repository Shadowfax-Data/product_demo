#!/usr/bin/env python3
import os
import snowflake.connector
from typing import List, Dict

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

def create_tables(conn: snowflake.connector.SnowflakeConnection):
    """Create SEC tables in Snowflake."""
    cursor = conn.cursor()
    
    # Table definitions with comments
    tables = {
        'SEC_NUMERICAL_DATA': """
            CREATE OR REPLACE TABLE SEC_NUMERICAL_DATA (
                adsh VARCHAR(20) COMMENT 'SEC Accession Number - Filing Identifier',
                tag VARCHAR(256) COMMENT 'Financial Element Tag/Metric Name',
                version VARCHAR(20) COMMENT 'Version of the Tag',
                ddate NUMBER(8,0) COMMENT 'Date of Data Point (YYYYMMDD)',
                qtrs NUMBER(2,0) COMMENT 'Number of Quarters Represented',
                uom VARCHAR(20) COMMENT 'Unit of Measure (e.g., USD, shares)',
                segments VARCHAR(1000) COMMENT 'Business Segment Identifiers',
                coreg VARCHAR(256) COMMENT 'Co-registrant Reference',
                value FLOAT COMMENT 'Numerical Value of the Data Point',
                footnote VARCHAR(512) COMMENT 'Reference to Associated Footnote'
            ) COMMENT = 'SEC Financial Statement Numerical Data Points'
        """,
        
        'SEC_PRESENTATION': """
            CREATE OR REPLACE TABLE SEC_PRESENTATION (
                adsh VARCHAR(20) COMMENT 'SEC Accession Number - Filing Identifier',
                report NUMBER(4,0) COMMENT 'Report Index Number',
                line NUMBER(4,0) COMMENT 'Line Number within Report',
                stmt VARCHAR(2) COMMENT 'Financial Statement Type Code',
                inpth NUMBER(1,0) COMMENT 'Indicates if Item is a Path Element',
                rfile VARCHAR(1) COMMENT 'Report File Type',
                tag VARCHAR(256) COMMENT 'Financial Element Tag',
                version VARCHAR(20) COMMENT 'Version of the Tag',
                plabel VARCHAR(512) COMMENT 'Presentation Label',
                negating NUMBER(1,0) COMMENT 'Indicates if Value Should be Negated'
            ) COMMENT = 'SEC Financial Statement Presentation Information'
        """,
        
        'SEC_SUBMISSIONS': """
            CREATE OR REPLACE TABLE SEC_SUBMISSIONS (
                adsh VARCHAR(20) COMMENT 'SEC Accession Number - Filing Identifier',
                cik NUMBER(10,0) COMMENT 'Central Index Key (CIK)',
                name VARCHAR(150) COMMENT 'Entity Name',
                sic NUMBER(4,0) COMMENT 'Standard Industrial Classification',
                countryba VARCHAR(3) COMMENT 'Business Address Country',
                stprba VARCHAR(2) COMMENT 'Business Address State/Province',
                cityba VARCHAR(30) COMMENT 'Business Address City',
                zipba VARCHAR(10) COMMENT 'Business Address ZIP',
                bas1 VARCHAR(40) COMMENT 'Business Address Street 1',
                bas2 VARCHAR(40) COMMENT 'Business Address Street 2',
                baph VARCHAR(20) COMMENT 'Business Address Phone',
                countryma VARCHAR(3) COMMENT 'Mailing Address Country',
                stprma VARCHAR(2) COMMENT 'Mailing Address State/Province',
                cityma VARCHAR(30) COMMENT 'Mailing Address City',
                zipma VARCHAR(10) COMMENT 'Mailing Address ZIP',
                mas1 VARCHAR(40) COMMENT 'Mailing Address Street 1',
                mas2 VARCHAR(40) COMMENT 'Mailing Address Street 2',
                countryinc VARCHAR(3) COMMENT 'Country of Incorporation',
                stprinc VARCHAR(2) COMMENT 'State of Incorporation',
                ein NUMBER(10,0) COMMENT 'Employee Identification Number',
                former VARCHAR(150) COMMENT 'Former Name',
                changed DATE COMMENT 'Date of Name Change',
                afs VARCHAR(5) COMMENT 'Filer Status',
                wksi NUMBER(1,0) COMMENT 'Well-Known Seasoned Issuer Status',
                fye NUMBER(4,0) COMMENT 'Fiscal Year End (MMDD)',
                form VARCHAR(10) COMMENT 'SEC Form Type',
                period NUMBER(8,0) COMMENT 'Period End Date',
                fy NUMBER(4,0) COMMENT 'Fiscal Year',
                fp VARCHAR(2) COMMENT 'Fiscal Period',
                filed DATE COMMENT 'Filing Date',
                accepted TIMESTAMP COMMENT 'Acceptance Timestamp',
                prevrpt NUMBER(1,0) COMMENT 'Previous Report Flag',
                detail NUMBER(1,0) COMMENT 'Detail Index',
                instance VARCHAR(32) COMMENT 'Instance Document File Name',
                nciks NUMBER(4,0) COMMENT 'Number of Co-Registrants',
                aciks VARCHAR(120) COMMENT 'Additional CIKs'
            ) COMMENT = 'SEC Filing Submission Information'
        """,
        
        'SEC_TAGS': """
            CREATE OR REPLACE TABLE SEC_TAGS (
                tag VARCHAR(256) COMMENT 'Financial Element Tag',
                version VARCHAR(20) COMMENT 'Version of the Tag',
                custom NUMBER(1,0) COMMENT 'Custom Tag Indicator',
                abstract NUMBER(1,0) COMMENT 'Abstract Element Indicator',
                datatype VARCHAR(20) COMMENT 'Data Type',
                iord VARCHAR(1) COMMENT 'Item or Dimension',
                crdr VARCHAR(1) COMMENT 'Credit/Debit Type',
                tlabel VARCHAR(512) COMMENT 'Tag Label',
                doc VARCHAR(8192) COMMENT 'Documentation'
            ) COMMENT = 'SEC XBRL Tag Definitions and Documentation'
        """
    }
    
    # Create each table
    for table_name, create_stmt in tables.items():
        print(f"Creating table {table_name}...")
        cursor.execute(create_stmt)
    
    cursor.close()

def main():
    """Main function to set up Snowflake tables."""
    conn = get_snowflake_connection()
    try:
        create_tables(conn)
        print("Successfully created all SEC tables in Snowflake.")
    finally:
        conn.close()

if __name__ == '__main__':
    main()