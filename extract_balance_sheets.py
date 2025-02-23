import os
import re
import requests
import tabula
import pandas as pd
import numpy as np
from urllib.parse import urlparse
from datetime import datetime

def download_pdf(url, tmp_dir="/tmp"):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(tmp_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filepath
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return None

def extract_balance_sheet(pdf_path):
    try:
        print(f"Extracting tables from {pdf_path}")
        # Try first 10 pages only to speed up processing
        tables = []
        for page in range(1, 11):
            try:
                # Try different extraction methods
                page_tables = tabula.read_pdf(pdf_path, pages=page, multiple_tables=True, lattice=True)
                if not page_tables:
                    page_tables = tabula.read_pdf(pdf_path, pages=page, multiple_tables=True, stream=True)
                if page_tables:
                    tables.extend(page_tables)
            except Exception as e:
                print(f"Skipping page {page} due to error: {str(e)}")
        
        # Find the consolidated balance sheet table
        balance_sheet = None
        for i, table in enumerate(tables):
            if table is not None and not table.empty:
                # Convert all columns to string for easier searching
                table_str = table.astype(str)
                table_text = ' '.join(table_str.values.flatten()).upper()
                
                # Look for key indicators of balance sheet table
                if ('CONSOLIDATED BALANCE SHEETS' in table_text or
                    'CONSOLIDATED BALANCE SHEET' in table_text or
                    ('ASSETS' in table_text and 'LIABILITIES' in table_text)):
                    print(f"\nFound potential balance sheet in table {i+1}")
                    print("Table shape:", table.shape)
                    print("Table columns:", table.columns.tolist())
                    print("First few rows:")
                    print(table.head())
                    
                    # Try to merge split columns
                    if table.shape[1] >= 4:  # If we have multiple columns that might need merging
                        try:
                            # Create a new DataFrame with merged columns
                            merged_df = pd.DataFrame()
                            
                            # First column is usually account names
                            account_col = table.columns[0]
                            merged_df['Account'] = table[account_col]
                            
                            # Try to merge numeric columns that might be split
                            value_cols = []
                            current_value = []
                            
                            for col in table.columns[1:]:
                                col_values = table[col].astype(str)
                                # Check if this column contains numeric or currency values
                                if col_values.str.contains(r'[\d,.$()\-]').any():
                                    current_value.append(col)
                                    # If we have 2-3 columns that look like parts of the same number
                                    if len(current_value) in [2, 3]:
                                        # Merge the columns
                                        merged_values = table[current_value].apply(
                                            lambda x: ''.join(x.fillna('').astype(str)), axis=1
                                        )
                                        value_cols.append(f"Value_{len(value_cols)}")
                                        merged_df[value_cols[-1]] = merged_values
                                        current_value = []
                                elif current_value:
                                    # If we hit a non-numeric column and have pending values
                                    merged_values = table[current_value].apply(
                                        lambda x: ''.join(x.fillna('').astype(str)), axis=1
                                    )
                                    value_cols.append(f"Value_{len(value_cols)}")
                                    merged_df[value_cols[-1]] = merged_values
                                    current_value = []
                            
                            # Handle any remaining columns
                            if current_value:
                                merged_values = table[current_value].apply(
                                    lambda x: ''.join(x.fillna('').astype(str)), axis=1
                                )
                                value_cols.append(f"Value_{len(value_cols)}")
                                merged_df[value_cols[-1]] = merged_values
                            
                            print("\nMerged table shape:", merged_df.shape)
                            print("Merged columns:", merged_df.columns.tolist())
                            print("First few rows of merged table:")
                            print(merged_df.head())
                            
                            if merged_df.shape[1] >= 3:  # Should have account names and at least two value columns
                                balance_sheet = merged_df
                                break
                        except Exception as e:
                            print(f"Error merging columns: {str(e)}")
                            continue
        
        if balance_sheet is None:
            print(f"No suitable balance sheet found in {pdf_path}")
            return None
        
        # Basic cleanup of the table
        balance_sheet = balance_sheet.dropna(how='all')
        balance_sheet = balance_sheet.dropna(axis=1, how='all')
        
        return balance_sheet
    except Exception as e:
        print(f"Error extracting balance sheet from {pdf_path}: {str(e)}")
        return None

def clean_balance_sheet(df, quarter_info):
    print("\nCleaning balance sheet...")
    print("Initial columns:", df.columns.tolist())
    print("Initial shape:", df.shape)

    # Function to clean text
    def clean_text(text):
        if pd.isna(text):
            return ''
        text = str(text).strip()
        if text.lower() == 'nan':
            return ''
        text = text.replace('\r', ' ').replace('\n', ' ')
        return ' '.join(text.split())

    # Clean all cells and convert to string
    df = df.astype(str)
    for col in df.columns:
        df[col] = df[col].apply(clean_text)

    # Account column should be the first one named 'Account'
    account_col = 'Account'
    if account_col not in df.columns:
        print("Could not find account column")
        return None

    # Value columns should be all columns starting with 'Value_'
    value_cols = [col for col in df.columns if col.startswith('Value_')]
    if not value_cols:
        print("Could not identify value columns")
        return None

    print("\nAccount column:", account_col)
    print("Value columns:", value_cols)

    # Clean up account names
    df[account_col] = df[account_col].apply(clean_text)

    # Remove rows with unwanted content or empty accounts
    unwanted = ['consolidated', 'balance sheet', 'balance sheets', 'in thousands', 'as of', '(unaudited)', 'notes to']
    df = df[~df[account_col].str.lower().str.contains('|'.join(unwanted), regex=True, na=False)]
    df = df[df[account_col].str.strip() != '']

    print("\nShape after removing unwanted rows:", df.shape)

    # Function to find dates in text
    def extract_date_from_text(text):
        # Look for dates in various formats
        date_patterns = [
            r'(?:As of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}',
            r'(?:As of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}'
        ]
        
        text = text.lower()
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract just the month and year
                date_text = match.group(0)
                month_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', date_text, re.IGNORECASE)
                year_match = re.search(r'20\d{2}', date_text)
                if month_match and year_match:
                    return f"{month_match.group(1)} {year_match.group(0)}"
        return None

    # Clean up numeric values and try to find dates
    column_dates = {}
    for col in value_cols:
        print(f"\nProcessing column: {col}")
        # Look for dates in the column values
        col_text = ' '.join(df[col].dropna().astype(str))
        date = extract_date_from_text(col_text)
        if date:
            column_dates[col] = date
        
        # Convert string numbers to numeric format
        df[col] = df[col].str.strip('$').str.replace(',', '')
        # Handle parentheses for negative numbers
        df[col] = df[col].apply(lambda x: f"-{x.strip('()')}" if isinstance(x, str) and '(' in x and ')' in x else x)
        # Convert to numeric, replacing empty strings with NaN
        df[col] = df[col].replace(['', 'nan', 'None', 'NaN'], np.nan)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Rename columns with dates or use generic names
    new_columns = {}
    for i, col in enumerate(value_cols):
        if col in column_dates:
            new_columns[col] = column_dates[col]
        else:
            new_columns[col] = f"Value_{i+1}"

    # Rename the columns
    df = df.rename(columns=new_columns)

    # Add quarter information as the first column
    df.insert(0, 'Quarter', quarter_info)

    # Remove rows where all numeric values are NaN
    value_cols = [col for col in df.columns if col not in ['Quarter', 'Account']]
    df = df.dropna(subset=value_cols, how='all')

    print("\nFinal shape:", df.shape)
    print("Final columns:", df.columns.tolist())

    return df

def generate_markdown_tables(df):
    """
    Convert DataFrame to markdown tables, one table per quarter.
    Returns a string containing all markdown tables.
    """
    markdown_text = []
    
    # Get unique quarters
    quarters = df['Quarter'].unique()
    quarters.sort()  # Sort quarters chronologically
    
    # Define account categories and their headers
    categories = {
        'assets': {
            'header': 'Assets',
            'patterns': [
                'Cash and cash equivalents',
                'Short-term investments',
                'Accounts receivable',
                'Prepaid expenses',
                'Total current assets',
                'Long-term investments',
                'Property and equipment',
                'Operating lease right-of-use assets',
                'Goodwill',
                'Intangible assets',
                'Deferred commissions',
                'Other assets',
                'Total assets'
            ]
        },
        'liabilities': {
            'header': 'Liabilities',
            'patterns': [
                'Accounts payable',
                'Accrued expenses',
                'Operating lease liabilities',
                'Deferred revenue',
                'Total current liabilities',
                'Convertible senior notes',
                'Other liabilities',
                'Total liabilities'
            ]
        },
        'equity': {
            'header': "Stockholders' Equity",
            'patterns': [
                'Additional paid-in capital',
                'Accumulated other comprehensive',
                'Accumulated deficit',
                'Noncontrolling interest',
                'Total Snowflake Inc. stockholders\' equity',
                'Total stockholders\' equity',
                'Total liabilities and stockholders\' equity'
            ]
        }
    }
    
    for quarter in quarters:
        # Filter data for this quarter
        quarter_data = df[df['Quarter'] == quarter]
        
        # Create table header
        markdown_text.append(f"\n## {quarter} Consolidated Balance Sheet\n")
        
        # Get value columns (excluding Quarter and Account)
        value_cols = [col for col in quarter_data.columns if col not in ['Quarter', 'Account']]
        
        # Map column names to dates based on quarter
        date_mapping = {}
        if quarter == 'FY25 Q3':
            date_mapping = {
                'Amount 2': 'October 31, 2024',
                'Amount 3': 'July 31, 2024',
                'Amount 4': 'January 31, 2024'
            }
        elif quarter == 'FY25 Q2':
            date_mapping = {
                'Amount 2': 'July 31, 2024',
                'Amount 3': 'April 30, 2024',
                'Amount 4': 'January 31, 2024'
            }
        elif quarter == 'FY25 Q1':
            date_mapping = {
                'Amount 2': 'April 30, 2024',
                'Amount 3': 'January 31, 2024',
                'Amount 4': 'January 31, 2023'
            }
        
        # Create header row with proper dates
        header = "| Account |"
        for col in value_cols:
            header += f" {date_mapping.get(col, col)} |"
        markdown_text.append(header)
        
        # Create alignment row with correct number of columns
        align = "|:---|" + "---:|" * len(value_cols)
        markdown_text.append(align)
        
        # Add data rows by category
        for category, info in categories.items():
            markdown_text.append(f"\n**{info['header']}**")
            
            # Filter rows for this category
            for pattern in info['patterns']:
                matching_rows = quarter_data[quarter_data['Account'].str.contains(pattern, case=False, na=False)]
                for _, row in matching_rows.iterrows():
                    data_row = f"| {row['Account']} |"
                    for col in value_cols:
                        value = row[col]
                        if pd.isna(value):
                            formatted_value = ""
                        else:
                            # Format numbers with commas and handle negative values
                            formatted_value = "{:,.0f}".format(value)
                            if value < 0:
                                formatted_value = f"({formatted_value.replace('-', '')})"
                        data_row += f" {formatted_value} |"
                    markdown_text.append(data_row)
        
        markdown_text.append("\n*All amounts in thousands (000s)*")
        markdown_text.append("")  # Add blank line between tables
    
    return "\n".join(markdown_text)

def process_pdfs(urls):
    all_balance_sheets = []
    
    for url in urls:
        print(f"\nProcessing {url}")
        # Extract quarter information and fiscal year from URL
        url_parts = url.lower().split('/')
        quarter_info = None
        fiscal_year = None
        
        # Look for fiscal year and quarter information in URL parts
        for part in url_parts:
            # Look for fiscal year
            if 'fy' in part:
                year_match = re.search(r'fy(\d{2})', part.lower())
                if year_match:
                    fiscal_year = year_match.group(1)
            elif '202' in part:
                year_match = re.search(r'202(\d)', part)
                if year_match:
                    fiscal_year = str(int(year_match.group(1)) + 20)  # Convert 2025 to FY25
            
            # Look for quarter
            for q in ['q1', 'q2', 'q3', 'q4']:
                if q in part:
                    quarter = q.upper()
                    if fiscal_year:
                        quarter_info = f"FY{fiscal_year} {quarter}"
                        break
        
        if not quarter_info:
            # Try to extract year and quarter from filename
            filename = os.path.basename(url).lower()
            if 'fy' in filename:
                year_match = re.search(r'fy(\d{2})', filename)
                if year_match:
                    fiscal_year = year_match.group(1)
            elif '202' in filename:
                year_match = re.search(r'202(\d)', filename)
                if year_match:
                    fiscal_year = str(int(year_match.group(1)) + 20)  # Convert 2025 to FY25
            
            for q in ['q1', 'q2', 'q3', 'q4']:
                if q in filename:
                    quarter = q.upper()
                    if fiscal_year:
                        quarter_info = f"FY{fiscal_year} {quarter}"
                        break
        
        if not quarter_info:
            print(f"Could not determine quarter information from {url}")
            continue
            
        print(f"Identified quarter: {quarter_info}")
        pdf_path = download_pdf(url)
        if pdf_path:
            try:
                balance_sheet = extract_balance_sheet(pdf_path)
                if balance_sheet is not None:
                    # Clean and standardize the balance sheet
                    cleaned_bs = clean_balance_sheet(balance_sheet, quarter_info)
                    if cleaned_bs is not None:
                        all_balance_sheets.append(cleaned_bs)
                        print(f"Successfully extracted and cleaned balance sheet for {quarter_info}")
            finally:
                # Clean up downloaded PDF
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
    
    if not all_balance_sheets:
        print("No balance sheets were successfully extracted")
        return None
    
    # Combine all balance sheets
    combined_bs = pd.concat(all_balance_sheets, ignore_index=True)
    
    # Sort by quarter
    def quarter_sort_key(quarter_str):
        # Extract fiscal year and quarter number
        match = re.match(r'FY(\d+)\s+Q(\d)', quarter_str)
        if match:
            fy, q = match.groups()
            return (int(fy), int(q))
        return (0, 0)  # Default sort key if pattern doesn't match
    
    # Define account categories for sorting
    account_categories = {
        'assets': [
            'Cash and cash equivalents',
            'Short-term investments',
            'Accounts receivable',
            'Prepaid expenses and other current assets',
            'Total current assets',
            'Long-term investments',
            'Property and equipment',
            'Operating lease right-of-use assets',
            'Goodwill',
            'Intangible assets',
            'Deferred commissions',
            'Other assets',
            'Total assets'
        ],
        'liabilities': [
            'Accounts payable',
            'Accrued expenses',
            'Operating lease liabilities',
            'Deferred revenue',
            'Total current liabilities',
            'Convertible senior notes',
            'Other liabilities',
            'Total liabilities'
        ],
        'equity': [
            'Additional paid-in capital',
            'Accumulated other comprehensive',
            'Accumulated deficit',
            'Total Snowflake Inc. stockholders\' equity',
            'Noncontrolling interest',
            'Total stockholders\' equity',
            'Total liabilities and stockholders\' equity'
        ]
    }

    def get_account_category_and_order(account):
        account = account.lower()
        for category, patterns in account_categories.items():
            for i, pattern in enumerate(patterns):
                if pattern.lower() in account:
                    return category, i
        return 'other', 999

    # Sort by quarter, account category, and account order
    combined_bs['Quarter_Sort'] = combined_bs['Quarter'].apply(quarter_sort_key)
    combined_bs['Account_Category'] = combined_bs['Account'].apply(lambda x: get_account_category_and_order(x)[0])
    combined_bs['Account_Order'] = combined_bs['Account'].apply(lambda x: get_account_category_and_order(x)[1])
    
    combined_bs = combined_bs.sort_values(
        ['Quarter_Sort', 'Account_Category', 'Account_Order', 'Account']
    ).drop(['Quarter_Sort', 'Account_Category', 'Account_Order'], axis=1)
    
    # Clean up column names
    def extract_date_from_column(col_name):
        if col_name in ['Quarter', 'Account']:
            return col_name
        
        # Look for dates in the data
        date_patterns = [
            r'(?:As of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}',
            r'(?:As of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, col_name, re.IGNORECASE)
            if match:
                # Extract just the month and year
                date_text = match.group(0)
                month_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', date_text, re.IGNORECASE)
                year_match = re.search(r'20\d{2}', date_text)
                if month_match and year_match:
                    return f"{month_match.group(1)} {year_match.group(0)}"
        
        # If no date found, try to find a number
        if col_name.startswith('Value_'):
            return f"Amount {int(col_name.split('_')[1]) + 1}"
        
        return col_name
    
    # Rename columns with dates
    new_columns = {col: extract_date_from_column(col) for col in combined_bs.columns}
    combined_bs = combined_bs.rename(columns=new_columns)
    
    # Reorder columns to ensure Quarter and Account are first
    cols = ['Quarter', 'Account'] + [col for col in combined_bs.columns if col not in ['Quarter', 'Account']]
    combined_bs = combined_bs[cols]
    
    return combined_bs

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract consolidated balance sheets from Snowflake financial statement PDFs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example usage:
  python extract_balance_sheets.py \\
    --urls https://example.com/q1.pdf https://example.com/q2.pdf \\
    --output balance_sheets.csv
'''
    )
    
    parser.add_argument(
        '--urls',
        nargs='+',
        required=True,
        help='One or more URLs to Snowflake financial statement PDFs'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help='Output CSV file path'
    )

    args = parser.parse_args()

    balance_sheets = process_pdfs(args.urls)
    if balance_sheets is not None:
        # Save CSV file
        print(f"\nSaving balance sheets to {args.output}")
        balance_sheets.to_csv(args.output, index=False)
        
        # Generate and save markdown file
        markdown_path = os.path.join(os.path.dirname(args.output), 'balance_sheets.md')
        print(f"\nGenerating markdown tables...")
        markdown_content = generate_markdown_tables(balance_sheets)
        with open(markdown_path, 'w') as f:
            f.write(markdown_content)
        print(f"Balance sheets markdown saved to {markdown_path}")
        print("Done!")