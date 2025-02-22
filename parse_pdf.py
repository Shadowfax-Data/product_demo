#!/usr/bin/env python3

import tabula
import pandas as pd
import json
from pathlib import Path

def extract_balance_sheet(pdf_path):
    """
    Extract balance sheet table from the Snowflake quarterly report PDF.
    Returns a pandas DataFrame with the balance sheet data.
    """
    # Read all tables from the PDF
    tables = tabula.read_pdf(
        pdf_path,
        pages='all',
        multiple_tables=True,
        pandas_options={'header': None}
    )
    
    # Find the balance sheet table by looking for key indicators
    balance_sheet = None
    for table in tables:
        if table.shape[1] >= 3:  # Balance sheet typically has at least 3 columns
            # Convert all values to string for easier searching
            table_str = table.astype(str).values.flatten()
            # Look for balance sheet indicators
            if any('ASSETS' in str(val).upper() for val in table_str) and \
               any('LIABILITIES' in str(val).upper() for val in table_str):
                balance_sheet = table
                break
    
    if balance_sheet is None:
        raise ValueError("Could not find balance sheet table in the PDF")

    # Clean up the data
    # Remove any completely empty rows or columns
    balance_sheet = balance_sheet.dropna(how='all').dropna(axis=1, how='all')
    
    # Save the extracted data as JSON for the next step
    output_path = Path('/tmp/balance_sheet_data.json')
    balance_sheet.to_json(output_path, orient='records')
    print(f"Balance sheet data saved to {output_path}")
    
    return balance_sheet

if __name__ == '__main__':
    pdf_path = '/tmp/snowflake_quarterly_report.pdf'
    try:
        balance_sheet = extract_balance_sheet(pdf_path)
        print("Successfully extracted balance sheet data")
        print("\nFirst few rows of the extracted data:")
        print(balance_sheet.head())
    except Exception as e:
        print(f"Error extracting balance sheet: {e}")