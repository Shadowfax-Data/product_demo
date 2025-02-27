#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from snowflake.connector import connect

# Snowflake connection parameters
conn = connect(
    user=os.environ['SNOWFLAKE_USER'],
    password=os.environ['SNOWFLAKE_PASSWORD'],
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    warehouse='COMPUTE_WH',
    database='SHADOWFAX',
    schema='DEV',
    role='SHADOWFAX'
)

# Query to get egg inventory data
query = """
SELECT 
    report_date,
    egg_type,
    SUM(volume_30doz_cases_thousands) as total_volume
FROM SHADOWFAX.DEV.usda_weekly_egg_inventory
WHERE report_date BETWEEN '2025-01-01' AND '2025-02-28'
    AND egg_type NOT IN ('Total', 'Breaking Stock')  -- Exclude totals and breaking stock
    AND region = '6-Area'  -- Use only 6-Area totals
GROUP BY report_date, egg_type
ORDER BY report_date, egg_type;
"""

# Execute query and load into pandas
df = pd.read_sql(query, conn)

# Close connection
conn.close()

# Convert column names to lowercase
df.columns = df.columns.str.lower()

# Convert report_date to datetime
df['report_date'] = pd.to_datetime(df['report_date'])

# Set up the plot style
plt.style.use('bmh')  # Use a built-in style
plt.figure(figsize=(12, 8))

# Create line plot
sns.lineplot(
    data=df,
    x='report_date',
    y='total_volume',
    hue='egg_type',
    marker='o'
)

# Customize the plot
plt.title('USDA Weekly Shell Egg Inventory by Type (Jan-Feb 2025)', pad=20)
plt.xlabel('Report Date')
plt.ylabel('Volume (30-dozen cases in thousands)')

# Rotate x-axis labels for better readability
plt.xticks(rotation=45)

# Adjust legend
plt.legend(title='Egg Type', bbox_to_anchor=(1.05, 1), loc='upper left')

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the plot
plt.savefig('/workspace/egg_inventory_2025.png', dpi=300, bbox_inches='tight')
print("Plot saved as egg_inventory_2025.png")