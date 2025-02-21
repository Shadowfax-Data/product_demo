import pandas as pd
import os
import snowflake.connector
from urllib.request import urlretrieve

# Download URLs
META_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Pregnant_Women-meta.csv"
DATA_URL = "https://archive.org/download/20250128-cdc-datasets/Vaccination_Coverage_among_Pregnant_Women.csv"

# Local file paths
META_FILE = "../data/pregnant_women_vaccination_meta.csv"
DATA_FILE = "../data/pregnant_women_vaccination.csv"

# Download files if they don't exist
if not os.path.exists(META_FILE):
    urlretrieve(META_URL, META_FILE)
if not os.path.exists(DATA_FILE):
    urlretrieve(DATA_URL, DATA_FILE)

# Read metadata and data
meta_df = pd.read_csv(META_FILE)
data_df = pd.read_csv(DATA_FILE)

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

# Create cursor
cur = conn.cursor()

# Create table
create_table_sql = """
CREATE OR REPLACE TABLE PREGNANT_WOMEN_VACCINATION_COVERAGE (
    VACCINE VARCHAR COMMENT 'Type of vaccine administered',
    GEOGRAPHY_TYPE VARCHAR COMMENT 'Type of geographic region (e.g., States, National)',
    GEOGRAPHY VARCHAR COMMENT 'Specific geographic location',
    SURVEY_YEAR NUMBER COMMENT 'Survey year or influenza season',
    DIMENSION_TYPE VARCHAR COMMENT 'Type of demographic dimension (e.g., Race and Ethnicity)',
    DIMENSION VARCHAR COMMENT 'Specific demographic category within the dimension',
    ESTIMATE_PCT FLOAT COMMENT 'Estimated vaccination coverage percentage',
    CONFIDENCE_INTERVAL VARCHAR COMMENT '95% Confidence Interval range',
    SAMPLE_SIZE FLOAT COMMENT 'Number of respondents in the sample'
) COMMENT = 'Vaccination coverage data among pregnant women across different demographics, locations, and years'
"""

cur.execute(create_table_sql)

# Clean and prepare data
data_df = data_df.rename(columns={
    'Survey Year/Influenza Season': 'SURVEY_YEAR',
    'Geography Type': 'GEOGRAPHY_TYPE',
    'Geography': 'GEOGRAPHY',
    'Dimension Type': 'DIMENSION_TYPE',
    'Dimension': 'DIMENSION',
    'Estimate (%)': 'ESTIMATE_PCT',
    '95% CI (%)': 'CONFIDENCE_INTERVAL',
    'Sample Size': 'SAMPLE_SIZE',
    'Vaccine': 'VACCINE'
})

# Handle special values and clean data
data_df['ESTIMATE_PCT'] = pd.to_numeric(data_df['ESTIMATE_PCT'].replace(['NR*', 'NR', '--'], None), errors='coerce')
data_df['SAMPLE_SIZE'] = pd.to_numeric(data_df['SAMPLE_SIZE'], errors='coerce')

# Fill NaN values
data_df = data_df.fillna('')

# Write data to CSV for bulk loading
temp_csv = '../data/pregnant_women_temp.csv'
data_df.to_csv(temp_csv, index=False)

# Load data into Snowflake
cur.execute("PUT file://" + temp_csv + " @%PREGNANT_WOMEN_VACCINATION_COVERAGE")
cur.execute("""
    COPY INTO PREGNANT_WOMEN_VACCINATION_COVERAGE 
    FROM @%PREGNANT_WOMEN_VACCINATION_COVERAGE 
    FILE_FORMAT = (
        TYPE = CSV 
        SKIP_HEADER = 1
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    )
""")

# Clean up
os.remove(temp_csv)

# Close connections
cur.close()
conn.close()

print("Data loaded successfully into PREGNANT_WOMEN_VACCINATION_COVERAGE table")