import pandas as pd
import os
import snowflake.connector
from urllib.request import urlretrieve
import numpy as np

# Download URLs
META_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_and_Exemptions_among_Kindergartners-meta.csv"
DATA_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_and_Exemptions_among_Kindergartners.csv"

# Local file paths
META_FILE = "/workspace/data/kindergartners_vaccination_meta.csv"
DATA_FILE = "/workspace/data/kindergartners_vaccination.csv"

# Download files
def download_files():
    if not os.path.exists('/workspace/data'):
        os.makedirs('/workspace/data')
    
    urlretrieve(META_URL, META_FILE)
    urlretrieve(DATA_URL, DATA_FILE)

# Create Snowflake connection
def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'],
        password=os.environ['SNOWFLAKE_PASSWORD'],
        warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
        database='CDC_DATASET',
        schema='PUBLIC',
        role=os.environ['SNOWFLAKE_ROLE']
    )

# Create table
def create_table(conn):
    create_table_sql = """
    CREATE OR REPLACE TABLE KINDERGARTNERS_VACCINATION_COVERAGE (
        VACCINE_OR_EXEMPTION VARCHAR(50) COMMENT 'Indicates if the record is for a vaccine or exemption',
        DOSE VARCHAR(50) COMMENT 'Specific dose information for exemptions',
        GEOGRAPHY_TYPE VARCHAR(50) COMMENT 'Type of geographic region (States, Local Areas, etc.)',
        GEOGRAPHY VARCHAR(100) COMMENT 'Name of the geographic location',
        SCHOOL_YEAR VARCHAR(10) COMMENT 'Academic year of the data',
        ESTIMATE_PERCENTAGE FLOAT COMMENT 'Estimated vaccination coverage or exemption percentage',
        POPULATION_SIZE NUMBER COMMENT 'Total population size',
        PERCENT_SURVEYED FLOAT COMMENT 'Percentage of population surveyed',
        FOOTNOTES VARCHAR(1000) COMMENT 'Additional notes about the data',
        NUMBER_OF_EXEMPTIONS NUMBER COMMENT 'Number of exemptions granted',
        SURVEY_TYPE VARCHAR(50) COMMENT 'Type of survey conducted'
    )
    COMMENT = 'Vaccination coverage and exemption rates among kindergartners in the United States'
    """
    
    conn.cursor().execute(create_table_sql)

# Load data
def load_data():
    # Download files
    download_files()
    
    # Read data
    df = pd.read_csv(DATA_FILE)
    
    # Clean and prepare data
    df = df.replace(['NR', 'NR*', '--', '†', 'NReq'], np.nan)
    
    # Convert percentage strings to floats
    def safe_convert_percentage(val):
        if pd.isna(val):
            return None
        try:
            return float(str(val).rstrip('%'))
        except:
            return None
    
    df['Estimate (%)'] = df['Estimate (%)'].apply(safe_convert_percentage)
    df['Percent Surveyed'] = df['Percent Surveyed'].apply(safe_convert_percentage)
    
    # Convert numeric columns
    df['Population Size'] = pd.to_numeric(df['Population Size'], errors='coerce')
    df['Number of Exemptions'] = pd.to_numeric(df['Number of Exemptions'], errors='coerce')
    
    # Connect to Snowflake and load data
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    
    # Create table
    create_table(conn)
    
    # Write data to Snowflake
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO KINDERGARTNERS_VACCINATION_COVERAGE (
            VACCINE_OR_EXEMPTION, DOSE, GEOGRAPHY_TYPE, GEOGRAPHY,
            SCHOOL_YEAR, ESTIMATE_PERCENTAGE, POPULATION_SIZE,
            PERCENT_SURVEYED, FOOTNOTES, NUMBER_OF_EXEMPTIONS,
            SURVEY_TYPE
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['Vaccine/Exemption'] if pd.notna(row.get('Vaccine/Exemption')) else None,
            row['Dose'] if pd.notna(row.get('Dose')) else None,
            row['Geography Type'] if pd.notna(row.get('Geography Type')) else None,
            row['Geography'] if pd.notna(row.get('Geography')) else None,
            row['School Year'] if pd.notna(row.get('School Year')) else None,
            row['Estimate (%)'] if pd.notna(row.get('Estimate (%)')) else None,
            row['Population Size'] if pd.notna(row.get('Population Size')) else None,
            row['Percent Surveyed'] if pd.notna(row.get('Percent Surveyed')) else None,
            row['Footnotes'] if pd.notna(row.get('Footnotes')) else None,
            row['Number of Exemptions'] if pd.notna(row.get('Number of Exemptions')) else None,
            row['Survey Type'] if pd.notna(row.get('Survey Type')) else None
        ))
    
    conn.close()

if __name__ == "__main__":
    load_data()