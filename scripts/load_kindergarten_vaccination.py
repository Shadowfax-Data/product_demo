import os
import pandas as pd
from snowflake.connector import connect
from snowflake.connector.pandas_tools import write_pandas

# Snowflake connection parameters from environment variables
snowflake_config = {
    'user': os.environ['SNOWFLAKE_USER'],
    'password': os.environ['SNOWFLAKE_PASSWORD'],
    'account': os.environ['SNOWFLAKE_ACCOUNT'],
    'warehouse': os.environ['SNOWFLAKE_WAREHOUSE'],
    'database': 'CDC_DATASET',
    'schema': 'PUBLIC',
    'role': os.environ['SNOWFLAKE_ROLE']
}

# Create Snowflake connection
conn = connect(**snowflake_config)
cursor = conn.cursor()

# Create table SQL
create_table_sql = """
CREATE OR REPLACE TRANSIENT TABLE CDC_DATASET.PUBLIC.KINDERGARTEN_VACCINATION_COVERAGE (
    VACCINE_OR_EXEMPTION VARCHAR NOT NULL COMMENT 'Type of vaccine or exemption being reported',
    DOSE VARCHAR COMMENT 'Specific dose information if applicable',
    GEOGRAPHY_TYPE VARCHAR NOT NULL COMMENT 'Type of geographic region (e.g., States)',
    GEOGRAPHY VARCHAR NOT NULL COMMENT 'Name of the geographic region',
    SCHOOL_YEAR VARCHAR NOT NULL COMMENT 'Academic year of the reported data',
    COVERAGE_ESTIMATE FLOAT COMMENT 'Estimated vaccination coverage or exemption percentage',
    POPULATION_SIZE INTEGER COMMENT 'Total kindergarten population in the geographic area',
    PERCENT_SURVEYED FLOAT COMMENT 'Percentage of population included in the survey',
    FOOTNOTES VARCHAR COMMENT 'Additional notes or clarifications about the data',
    EXEMPTION_COUNT INTEGER COMMENT 'Number of exemptions granted',
    SURVEY_TYPE VARCHAR COMMENT 'Type of survey methodology used'
) COMMENT = 'CDC Kindergarten Vaccination Coverage and Exemptions data tracking vaccination rates and exemptions for kindergarten students across different regions and years';
"""

# Execute create table
cursor.execute(create_table_sql)

# Read CSV data
df = pd.read_csv('/tmp/Vaccination_Coverage_and_Exemptions_among_Kindergartners.csv')

# Clean and prepare data
df.columns = ['VACCINE_OR_EXEMPTION', 'DOSE', 'GEOGRAPHY_TYPE', 'GEOGRAPHY', 
              'SCHOOL_YEAR', 'COVERAGE_ESTIMATE', 'POPULATION_SIZE', 
              'PERCENT_SURVEYED', 'FOOTNOTES', 'EXEMPTION_COUNT', 'SURVEY_TYPE']

# Convert percentage string to float where possible
df['COVERAGE_ESTIMATE'] = pd.to_numeric(df['COVERAGE_ESTIMATE'].str.replace('†', ''), errors='coerce')

# Write data to Snowflake
success, nchunks, nrows, _ = write_pandas(
    conn=conn,
    df=df,
    table_name='KINDERGARTEN_VACCINATION_COVERAGE',
    database='CDC_DATASET',
    schema='PUBLIC'
)

print(f"Data loaded successfully: {success}")
print(f"Number of chunks: {nchunks}")
print(f"Number of rows: {nrows}")

cursor.close()
conn.close()