import pandas as pd
import snowflake.connector
import os
from snowflake.connector.pandas_tools import write_pandas

# Read the SQL script
with open('/workspace/sql/create_adult_vaccination_coverage.sql', 'r') as file:
    create_table_sql = file.read()

# Create Snowflake connection
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
cursor.execute(create_table_sql)

# Read the data
df = pd.read_csv('/workspace/data/adults_vaccination_data.csv')

# Replace special values with None/NULL
df = df.replace(['NR', '*', '--'], None)

# Rename columns to match schema
column_mapping = {
    'Vaccine': 'VACCINE',
    'Dose': 'DOSE',
    'Geography Type': 'GEOGRAPHY_TYPE',
    'Geography': 'GEOGRAPHY',
    'FIPS': 'FIPS',
    'Survey Year': 'SURVEY_YEAR',
    'Dimension Type': 'DIMENSION_TYPE',
    'Dimension': 'DIMENSION',
    'Estimate (%)': 'ESTIMATE_PERCENTAGE',
    '95% CI (%)': 'CONFIDENCE_INTERVAL',
    'Sample Size': 'SAMPLE_SIZE'
}
df = df.rename(columns=column_mapping)

# Write data to Snowflake
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