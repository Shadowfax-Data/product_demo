#!/usr/bin/env python3

import argparse
import os
import requests
from urllib.parse import urlparse
import PyPDF2
import re
import camelot
import pandas as pd
import numpy as np

def download_pdf(url, output_dir):
    """
    Download a PDF file from a URL and save it to the specified directory.
    Returns the path to the downloaded file.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Extract filename from URL or use a default name
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename.endswith('.pdf'):
            filename = 'financial_statement.pdf'
        
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return output_path
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error downloading PDF: {str(e)}")

def find_balance_sheet_page(pdf_path):
    """
    Find the page number containing the consolidated balance sheet.
    Returns the page number (0-based index) or raises an exception if not found.
    """
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            # Look for the actual balance sheet table, not just the TOC reference
            if ('CONDENSED CONSOLIDATED BALANCE SHEETS' in text.upper() and 
                ('(in thousands)' in text.lower() or 
                 'assets' in text.lower() or 
                 'liabilities' in text.lower())):
                return page_num
            
    raise Exception("Could not find consolidated balance sheet in the PDF")

def extract_page_to_pdf(input_pdf_path, page_number, output_pdf_path):
    """
    Extract a specific page from the input PDF and save it as a new PDF file.
    """
    with open(input_pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        if page_number >= len(pdf_reader.pages):
            raise Exception(f"Page number {page_number} is out of range")
        
        page = pdf_reader.pages[page_number]
        pdf_writer.add_page(page)
        
        with open(output_pdf_path, 'wb') as output_file:
            pdf_writer.write(output_file)

def extract_table_data(pdf_path):
    """
    Extract table data from the PDF using Camelot.
    Returns a cleaned pandas DataFrame.
    """
    # Extract tables using Camelot with lattice mode
    tables = camelot.read_pdf(pdf_path, pages='1', flavor='lattice')
    
    if len(tables) == 0:
        # Try stream mode if lattice mode fails
        tables = camelot.read_pdf(pdf_path, pages='1', flavor='stream')
    
    if len(tables) == 0:
        raise Exception("No tables found in the PDF")
    
    # Get the largest table (usually the balance sheet)
    largest_table = max(tables, key=lambda t: len(t.df))
    df = largest_table.df
    
    # Clean up the table data
    df = clean_table_data(df)
    
    return df

def clean_table_data(df):
    """
    Clean and validate the extracted table data.
    """
    # Remove empty rows and columns
    df = df.replace('', np.nan)
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    
    # Find the row with the dates (usually contains months)
    date_row_idx = df.apply(lambda row: row.astype(str).str.contains('April|January|July|October').any(), axis=1)
    date_row_idx = date_row_idx[date_row_idx].index[0]
    
    # Extract dates and set as column headers
    dates = df.iloc[date_row_idx]
    valid_dates = [d for d in dates if isinstance(d, str) and any(month in d for month in ['April', 'January', 'July', 'October'])]
    
    # Keep only the columns we need (first column for line items and date columns)
    date_indices = [i for i, d in enumerate(dates) if isinstance(d, str) and any(month in d for month in ['April', 'January', 'July', 'October'])]
    keep_cols = [0] + date_indices  # 0 for line items column
    df = df.iloc[:, keep_cols]
    
    # Set new column names
    df.columns = ['line_item'] + valid_dates
    
    # Remove header rows
    df = df.iloc[date_row_idx + 1:]
    
    # Clean up whitespace and special characters
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].str.strip()
            df[col] = df[col].str.replace('\n', ' ', regex=False)
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
    
    # Remove any rows that are just horizontal lines or spaces
    df = df[~df['line_item'].str.contains('^[-\s]*$', regex=True, na=False)]
    
    # Remove any remaining empty rows
    df = df.dropna(how='all')
    
    # Clean up numeric columns
    numeric_cols = df.columns[1:]  # All columns except line_item
    for col in numeric_cols:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].str.replace('$', '', regex=False)
            df[col] = df[col].str.replace(',', '', regex=False)
            df[col] = df[col].str.replace('(', '-', regex=False)
            df[col] = df[col].str.replace(')', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Add category column based on indentation and line items
    df['category'] = ''
    current_category = ''
    
    for idx, row in df.iterrows():
        line_item = str(row['line_item']).strip()
        # Check for main categories
        if any(keyword in line_item.lower() for keyword in ['assets', 'liabilities', 'equity', 'total']):
            if line_item.endswith(':'):
                current_category = line_item.rstrip(':')
            elif line_item.lower().startswith('total'):
                current_category = line_item
        df.at[idx, 'category'] = current_category
    
    # Clean up line items (remove leading/trailing whitespace and colons)
    df['line_item'] = df['line_item'].str.strip().str.rstrip(':')
    
    # Reorder columns to match required format
    date_cols = [col for col in df.columns if col not in ['line_item', 'category']]
    result_dfs = []
    
    for date_col in date_cols:
        temp_df = df[['category', 'line_item', date_col]].copy()
        temp_df.columns = ['category', 'line_item', 'amount']
        temp_df['fiscal_quarter'] = date_col
        temp_df = temp_df[['fiscal_quarter', 'category', 'line_item', 'amount']]
        result_dfs.append(temp_df)
    
    final_df = pd.concat(result_dfs, ignore_index=True)
    
    # Remove rows that are just categories without amounts
    final_df = final_df[~(final_df['line_item'].str.endswith(':') & final_df['amount'].isna())]
    
    return final_df
    
    # Clean up line items (remove leading/trailing whitespace and colons)
    df['line_item'] = df['line_item'].str.strip().str.rstrip(':')
    
    # Reorder columns to match required format
    date_cols = [col for col in df.columns if col not in ['line_item', 'category']]
    result_dfs = []
    
    for date_col in date_cols:
        temp_df = df[['category', 'line_item', date_col]].copy()
        temp_df.columns = ['category', 'line_item', 'amount']
        temp_df['fiscal_quarter'] = date_col
        temp_df = temp_df[['fiscal_quarter', 'category', 'line_item', 'amount']]
        result_dfs.append(temp_df)
    
    final_df = pd.concat(result_dfs, ignore_index=True)
    return final_df

def main():
    parser = argparse.ArgumentParser(description='Extract financial data from Snowflake quarterly reports')
    parser.add_argument('url', help='URL of the PDF financial statement')
    parser.add_argument('--output', required=True, help='Output path for the CSV file')
    parser.add_argument('--tmp-dir', default='/tmp', help='Directory for temporary files')
    
    args = parser.parse_args()
    
    # Create temporary directory if it doesn't exist
    os.makedirs(args.tmp_dir, exist_ok=True)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Download the PDF
    print(f"Downloading PDF from {args.url}...")
    pdf_path = download_pdf(args.url, args.tmp_dir)
    print(f"PDF downloaded successfully to {pdf_path}")
    
    # Find the balance sheet page
    print("Locating balance sheet page...")
    balance_sheet_page = find_balance_sheet_page(pdf_path)
    print(f"Found balance sheet on page {balance_sheet_page + 1}")
    
    # Extract the balance sheet page to a new PDF
    balance_sheet_pdf = os.path.join(args.tmp_dir, 'balance_sheet.pdf')
    print(f"Extracting balance sheet page to {balance_sheet_pdf}...")
    extract_page_to_pdf(pdf_path, balance_sheet_page, balance_sheet_pdf)
    print("Balance sheet page extracted successfully")
    
    # Extract and clean table data
    print("Extracting and cleaning table data...")
    df = extract_table_data(balance_sheet_pdf)
    print("Table data extracted and cleaned successfully")
    
    # Validate the extracted data
    if df.empty:
        raise Exception("No valid data was extracted from the table")
    
    # Format fiscal quarter consistently (e.g., "Q1 FY2025" for April 30, 2024)
    def format_fiscal_quarter(date_str):
        year = int(date_str[-4:])
        if 'January' in date_str:
            return f'Q4 FY{year}'
        elif 'April' in date_str:
            return f'Q1 FY{year + 1}'
        elif 'July' in date_str:
            return f'Q2 FY{year + 1}'
        elif 'October' in date_str:
            return f'Q3 FY{year + 1}'
        return date_str
    
    df['fiscal_quarter'] = df['fiscal_quarter'].apply(format_fiscal_quarter)
    
    # Format amounts as integers without decimals
    df['amount'] = df['amount'].apply(lambda x: int(float(str(x).replace(',', ''))) if pd.notna(x) else x)
    
    # Remove rows where amount is null
    df = df[pd.notna(df['amount'])]
    
    # Save to CSV
    df.to_csv(args.output, index=False)
    print(f"\nData saved to {args.output}")
    print(f"Total rows: {len(df)}")
    print("\nSample of extracted data:")
    print(df.head())

if __name__ == '__main__':
    main()