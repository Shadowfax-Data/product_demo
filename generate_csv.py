#!/usr/bin/env python3

import pandas as pd
import json
from pathlib import Path

def generate_csv():
    """
    Convert the extracted balance sheet data from JSON to a properly structured CSV file.
    """
    # Read the JSON data
    json_path = Path('/tmp/balance_sheet_data.json')
    if not json_path.exists():
        raise FileNotFoundError("Balance sheet data JSON file not found. Run parse_pdf.py first.")
    
    df = pd.read_json(json_path, orient='records')
    
    # Clean up the data
    # Replace NaN with empty string
    df = df.fillna('')
    
    # Clean up column names - first row usually contains the dates
    dates = df.iloc[0]
    # Convert column names to proper format
    df.columns = [f'col_{i}' for i in range(len(df.columns))]
    
    # First column is typically the account names
    df = df.rename(columns={'col_0': 'Account'})
    
    # Use the dates from the first row for other columns
    date_columns = {}
    for i in range(1, len(df.columns)):
        col_name = f'col_{i}'
        date_val = str(dates[col_name]).strip()
        if date_val:
            date_columns[col_name] = date_val
    
    df = df.rename(columns=date_columns)
    
    # Remove the first row (dates) since we used it for column names
    df = df.iloc[1:]
    
    # Clean up the data
    # Remove any rows where Account is empty or contains only whitespace
    df = df[df['Account'].str.strip() != '']
    
    # Save to CSV
    output_path = Path('/workspace/balance_sheets.csv')
    df.to_csv(output_path, index=False)
    print(f"Balance sheet data saved to {output_path}")
    
    return df

if __name__ == '__main__':
    try:
        df = generate_csv()
        print("\nFirst few rows of the generated CSV data:")
        print(df.head())
    except Exception as e:
        print(f"Error generating CSV: {e}")