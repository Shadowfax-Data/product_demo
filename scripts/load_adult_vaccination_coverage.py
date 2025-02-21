import os
import pandas as pd
from snowflake.connector import connect
from snowflake.connector.pandas_tools import write_pandas

# Read the CSV file
df = pd.read_csv('/tmp/Vaccination_Coverage_among_Adults_18_Years.csv')

# Handle special values
df['Estimate (%)'] = pd.to_numeric(df['Estimate (%)'].replace(['NR', '*'], None))
df['Sample Size'] = pd.to_numeric(df['Sample Size'].replace(['NR', '*'], None))

# Clean column names and rename specific columns
df.columns = [col.upper().replace(' ', '_').replace('(', '').replace(')', '').replace('%', 'PERCENT').replace('/', '_')
              for col in df.columns]
print("Columns after cleaning:", list(df.columns))
df = df.rename(columns={'95PERCENT_CI_PERCENT': 'CI_95_PERCENT'})

# Create Snowflake connection
conn = connect(
    user=os.environ['SNOWFLAKE_USER'],
    password=os.environ['SNOWFLAKE_PASSWORD'],
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
    database='CDC_DATASET',
    schema='PUBLIC',
    role=os.environ['SNOWFLAKE_ROLE']
)

# Create the table
create_table_sql = """
CREATE OR REPLACE TRANSIENT TABLE ADULT_VACCINATION_COVERAGE (
    VACCINE VARCHAR(100) COMMENT 'Type of vaccine administered',
    DOSE VARCHAR(50) COMMENT 'Specific dose type or schedule of the vaccine',
    GEOGRAPHY_TYPE VARCHAR(50) COMMENT 'Level of geographic aggregation (e.g., States/Local Areas)',
    GEOGRAPHY VARCHAR(100) COMMENT 'Name of the geographic area',
    FIPS VARCHAR(10) COMMENT 'Federal Information Processing Standards (FIPS) code for the geographic area',
    SURVEY_YEAR NUMBER COMMENT 'Year the survey was conducted',
    DIMENSION_TYPE VARCHAR(50) COMMENT 'Type of population dimension being measured (e.g., age group)',
    DIMENSION VARCHAR(100) COMMENT 'Specific category within the dimension type',
    ESTIMATE_PERCENT FLOAT COMMENT 'Estimated vaccination coverage percentage',
    CI_95_PERCENT VARCHAR(50) COMMENT '95% Confidence Interval for the estimate',
    SAMPLE_SIZE NUMBER COMMENT 'Number of individuals in the sample'
) COMMENT = 'CDC Vaccination Coverage among Adults 18 Years and Older - Contains estimates of vaccination coverage for various vaccines among adults across different geographic areas, years, and population dimensions'
"""

cursor = conn.cursor()
cursor.execute(create_table_sql)

# Load the data
success, nchunks, nrows, _ = write_pandas(
    conn=conn,
    df=df,
    table_name='ADULT_VACCINATION_COVERAGE',
    database='CDC_DATASET',
    schema='PUBLIC'
)

print(f"Data loaded successfully: {success}")
print(f"Number of chunks: {nchunks}")
print(f"Number of rows: {nrows}")

conn.close()