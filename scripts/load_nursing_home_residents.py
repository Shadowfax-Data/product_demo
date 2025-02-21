import pandas as pd
import os
import snowflake.connector
from urllib.request import urlretrieve

# Download URLs
META_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Nursing_Home_Residents-meta.csv"
DATA_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Nursing_Home_Residents.csv"

# Download files
meta_file = "/workspace/data/nursing_home_residents_meta.csv"
data_file = "/workspace/data/nursing_home_residents.csv"

urlretrieve(META_URL, meta_file)
urlretrieve(DATA_URL, data_file)

# Read metadata and data
meta_df = pd.read_csv(meta_file)
data_df = pd.read_csv(data_file)

# Connect to Snowflake
conn = snowflake.connector.connect(
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    user=os.environ['SNOWFLAKE_USER'],
    password=os.environ['SNOWFLAKE_PASSWORD'],
    warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
    database='CDC_DATASET',
    schema='PUBLIC',
    role=os.environ['SNOWFLAKE_ROLE']
)

# Create table
create_table_sql = """
CREATE OR REPLACE TABLE NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE (
    VACCINE VARCHAR COMMENT 'Type of vaccine administered',
    GEOGRAPHY_TYPE VARCHAR COMMENT 'Type of geographic region (e.g., HHS Regions/National)',
    GEOGRAPHY VARCHAR COMMENT 'Specific geographic location',
    SURVEY_YEAR VARCHAR COMMENT 'Survey year or influenza season',
    DIMENSION_TYPE VARCHAR COMMENT 'Type of demographic dimension (e.g., Age, Marital Status)',
    DIMENSION VARCHAR COMMENT 'Specific demographic category',
    ESTIMATE_PERCENTAGE NUMBER(5,1) COMMENT 'Vaccination coverage estimate percentage',
    POPULATION_SIZE NUMBER COMMENT 'Size of the population in the demographic category'
) COMMENT = 'Vaccination coverage data among nursing home residents across different demographics and geographic regions'
"""

cursor = conn.cursor()
cursor.execute(create_table_sql)

# Process the data
data_df['ESTIMATE_PERCENTAGE'] = pd.to_numeric(data_df['Estimate (%)'].replace('NA', None), errors='coerce')
data_df['POPULATION_SIZE'] = pd.to_numeric(data_df['Population Size'], errors='coerce')

# Prepare data for loading
processed_df = data_df.rename(columns={
    'Vaccine': 'VACCINE',
    'Geography Type': 'GEOGRAPHY_TYPE',
    'Geography': 'GEOGRAPHY',
    'Survey Year/Influenza Season': 'SURVEY_YEAR',
    'Dimension Type': 'DIMENSION_TYPE',
    'Dimension': 'DIMENSION'
})[['VACCINE', 'GEOGRAPHY_TYPE', 'GEOGRAPHY', 'SURVEY_YEAR', 
    'DIMENSION_TYPE', 'DIMENSION', 'ESTIMATE_PERCENTAGE', 'POPULATION_SIZE']]

processed_df.to_csv('/workspace/data/nursing_home_residents_processed.csv', index=False)

# Create stage and load data into Snowflake
cursor.execute("CREATE OR REPLACE STAGE NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '\"' SKIP_HEADER = 1)")

# Use snowflake-connector-python's PUT command
with open('/workspace/data/nursing_home_residents_processed.csv', 'rb') as f:
    cursor.execute("PUT file:///workspace/data/nursing_home_residents_processed.csv @NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE")

# Copy from stage into table
cursor.execute("""
COPY INTO NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE
FROM @NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE/nursing_home_residents_processed.csv.gz
FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1)
ON_ERROR = 'CONTINUE'
PURGE = TRUE
""")

cursor.close()
conn.close()

print("Data loaded successfully into Snowflake!")