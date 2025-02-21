import pandas as pd
import snowflake.connector
import os
from urllib.request import urlretrieve
import sys
import numpy as np

# Download URLs
meta_url = "https://archive.org/download/20250128-cdc-datasets/Vaccination_coverage_among_children_19_35_months_of_age_for_selected_diseases_by_race_Hispanic_origin_poverty_level_and_location_of_residence_in_metropolitan_area_meta.csv"
data_url = "https://archive.org/download/20250128-cdc-datasets/Vaccination_coverage_among_children_19_35_months_of_age_for_selected_diseases_by_race_Hispanic_origin_poverty_level_and_location_of_residence_in_metropolitan_area_.csv"

# Download files
meta_file = "/workspace/data/children_19_35_months_by_race_meta.csv"
data_file = "/workspace/data/children_19_35_months_by_race.csv"

urlretrieve(meta_url, meta_file)
urlretrieve(data_url, data_file)

# Read the data
df = pd.read_csv(data_file)
meta_df = pd.read_csv(meta_file)

# Clean column names
df.columns = df.columns.str.strip().str.upper().str.replace(' ', '_').str.replace('[^A-Z0-9_]', '')

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

# Create the table
cursor = conn.cursor()

create_table_sql = """
CREATE OR REPLACE TABLE CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE (
    YEAR VARCHAR COMMENT 'Year of data collection',
    RACE_ETHNICITY VARCHAR COMMENT 'Race and ethnicity category',
    POVERTY_LEVEL VARCHAR COMMENT 'Poverty level category',
    RESIDENCE_LOCATION VARCHAR COMMENT 'Location of residence in metropolitan area',
    VACCINE_TYPE VARCHAR COMMENT 'Type of vaccine administered',
    COVERAGE_PERCENTAGE VARCHAR COMMENT 'Vaccination coverage percentage',
    CONFIDENCE_INTERVAL_LOW VARCHAR COMMENT 'Lower bound of 95% confidence interval',
    CONFIDENCE_INTERVAL_HIGH VARCHAR COMMENT 'Upper bound of 95% confidence interval',
    SAMPLE_SIZE VARCHAR COMMENT 'Number of children in the sample'
)
COMMENT = 'Vaccination coverage among children 19-35 months of age by race, Hispanic origin, poverty level, and metropolitan residence location'
"""

cursor.execute(create_table_sql)

# Prepare data for loading
df = df.replace(['--', 'NR', 'NR*'], np.nan)

# Convert numeric columns while preserving non-numeric values
for col in df.columns:
    try:
        df[col] = pd.to_numeric(df[col], errors='raise')
    except:
        pass  # Keep as string if conversion fails

# Write to CSV for bulk loading
temp_csv = "/workspace/data/temp_children_19_35_months_race.csv"
df.to_csv(temp_csv, index=False, header=False, na_rep='NULL', quoting=1, escapechar='\\', sep='|')

# Load data into Snowflake
cursor.execute("PUT file://" + temp_csv + " @%CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE")
cursor.execute("""
COPY INTO CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE 
FROM @%CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE 
FILE_FORMAT = (
    TYPE = CSV 
    FIELD_DELIMITER = '|'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
)""")

# Clean up
os.remove(temp_csv)
cursor.close()
conn.close()

print("Data loaded successfully into CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE table")