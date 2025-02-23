#!/usr/bin/env python3

import argparse
import os
import sys
import re
import requests
import tabula
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse
from PyPDF2 import PdfReader

def download_pdf(url: str, output_dir: str) -> str:
    """
    Download a PDF from a URL and save it to the specified directory.
    Returns the path to the downloaded file.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Extract filename from URL or use a default name
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or 'document.pdf'
        if not filename.endswith('.pdf'):
            filename += '.pdf'
            
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        return output_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
        return None

def download_pdfs(urls: List[str], output_dir: str) -> List[str]:
    """
    Download multiple PDFs and return list of successful downloads.
    """
    os.makedirs(output_dir, exist_ok=True)
    downloaded_files = []
    
    for url in urls:
        pdf_path = download_pdf(url, output_dir)
        if pdf_path:
            downloaded_files.append(pdf_path)
            print(f"Successfully downloaded: {pdf_path}")
        
    return downloaded_files

def extract_date_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract the statement date from the PDF using PyPDF2.
    Returns date in YYYY-MM-DD format.
    """
    try:
        reader = PdfReader(pdf_path)
        text = reader.pages[0].extract_text()
        
        # Look for dates in format "January 31, 2024" or similar
        date_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}'
        match = re.search(date_pattern, text)
        
        if match:
            from datetime import datetime
            date_str = match.group(0)
            date_obj = datetime.strptime(date_str, '%B %d, %Y')
            return date_obj.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Error extracting date from {pdf_path}: {e}", file=sys.stderr)
    return None

def clean_numeric_value(value: str) -> Optional[float]:
    """
    Clean numeric values from the balance sheet.
    Handles various formats including parentheses for negative numbers,
    different currency symbols, and scale indicators (K, M, B).
    """
    if pd.isna(value):
        return None
    
    value = str(value).strip()
    if not value or value.lower() in ['na', 'n/a', '-', '']:
        return None
        
    # Remove currency symbols and whitespace
    value = re.sub(r'[$€£¥]|\s', '', value)
    
    # Remove commas
    value = value.replace(',', '')
    
    # Handle parentheses (negative numbers)
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    
    # Handle scale indicators
    scale_multipliers = {
        'k': 1_000,
        'm': 1_000_000,
        'b': 1_000_000_000
    }
    
    match = re.match(r'^(-?\d+\.?\d*)(k|m|b)?$', value.lower())
    if match:
        number, scale = match.groups()
        try:
            result = float(number)
            if scale:
                result *= scale_multipliers[scale]
            return result
        except ValueError:
            return None
    
    try:
        return float(value)
    except ValueError:
        return None

def validate_balance_sheet_structure(df: pd.DataFrame) -> bool:
    """
    Validate the basic structure of a balance sheet.
    Returns True if the structure is valid, False otherwise.
    """
    if df is None or df.empty:
        return False
    
    # Check minimum required columns (description + at least one date)
    if df.shape[1] < 2:
        return False
    
    # Check for key balance sheet sections
    required_terms = [
        ['asset', 'assets'],
        ['liabilit', 'liabilities'],
        ['equity', 'stockholder', 'shareholder']
    ]
    
    first_col = df.iloc[:, 0].astype(str).str.lower()
    found_sections = [
        any(term in ' '.join(first_col) for term in section)
        for section in required_terms
    ]
    
    return all(found_sections)

def clean_and_validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the balance sheet data.
    Performs various data quality checks and cleaning operations.
    """
    if df is None or df.empty:
        return df
    
    # Store original column names
    original_cols = df.columns.tolist()
    
    # Clean description column
    df.iloc[:, 0] = df.iloc[:, 0].apply(lambda x: str(x).strip())
    
    # Remove rows where description is empty or just whitespace
    df = df[df.iloc[:, 0].str.strip().astype(bool)]
    
    # Clean numeric columns
    numeric_cols = df.columns[1:-1]  # Exclude description and Statement_Date
    for col in numeric_cols:
        df[col] = df[col].apply(clean_numeric_value)
    
    # Remove rows where all numeric values are NaN
    df = df.dropna(subset=numeric_cols, how='all')
    
    # Validate numeric values are within reasonable ranges
    for col in numeric_cols:
        # Convert to numeric, coercing errors to NaN
        df[col] = pd.to_numeric(df[col], errors='coerce')
        # Flag extreme values (above 1 trillion)
        extreme_mask = df[col].fillna(0).abs() > 1e12
        if extreme_mask.any():
            print(f"Warning: Extreme values found in column {col}", file=sys.stderr)
            df.loc[extreme_mask, col] = None
    
    # Check for data consistency
    for col in numeric_cols:
        # Check for consistent scale across values
        non_null_values = df[col].dropna()
        if len(non_null_values) > 0:
            max_scale_diff = non_null_values.abs().max() / non_null_values.abs().min()
            if max_scale_diff > 1e6:
                print(f"Warning: Inconsistent scales detected in column {col}", file=sys.stderr)
    
    # Restore original column order
    df = df[original_cols]
    
    return df

def extract_balance_sheet(pdf_path: str) -> Optional[pd.DataFrame]:
    """
    Extract consolidated balance sheet data from a PDF using Tabula.
    Returns a DataFrame with the balance sheet data.
    """
    def find_balance_sheet_page(pdf_path: str) -> List[int]:
        """Find pages that might contain the balance sheet."""
        reader = PdfReader(pdf_path)
        potential_pages = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text().lower()
            if any(term in text for term in [
                'consolidated balance sheets',
                'consolidated balance sheet',
                'condensed consolidated balance sheets',
                'condensed consolidated balance sheet',
                'balance sheets',
                'balance sheet'
            ]):
                potential_pages.append(i)
        return potential_pages if potential_pages else [1, 2, 3]  # Default to first few pages if not found
    try:
        # Find the page with the balance sheet
        target_page = find_balance_sheet_page(pdf_path)
        
        # Try different extraction methods on all potential pages
        tables = []
        
        for page in target_page:
            # Method 1: Stream mode with full page area
            tables.extend(tabula.read_pdf(
                pdf_path,
                pages=page,
                multiple_tables=True,
                pandas_options={'header': None},
                stream=True,
                guess=True,
                area=[0, 0, 100, 100],
                relative_area=True
            ))
            
            # Method 2: Lattice mode with full page area
            tables.extend(tabula.read_pdf(
                pdf_path,
                pages=page,
                multiple_tables=True,
                pandas_options={'header': None},
                lattice=True,
                guess=False,
                area=[0, 0, 100, 100],
                relative_area=True
            ))
        
        # Remove empty tables and tables with less than 3 columns
        tables = [t for t in tables if not t.empty and t.shape[1] >= 3]
        
        # Find the balance sheet table
        balance_sheet = None
        for table in tables:
            if table.shape[0] > 5:  # Ensure table has enough rows
                # Convert to string and check for balance sheet indicators
                table_text = ' '.join(table.astype(str).values.flatten()).lower()
                
                # Look for common balance sheet terms
                if (('assets' in table_text or 'cash and cash equivalents' in table_text) and
                    ('liabilities' in table_text or 'stockholders' in table_text)):
                    # Check if table has numeric values
                    numeric_values = table.apply(lambda x: pd.to_numeric(x.astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce')).notna().sum().sum()
                    if numeric_values > 5:  # At least 5 numeric values
                        balance_sheet = table
                        break
        
        if balance_sheet is None:
            print(f"No balance sheet found in {pdf_path}", file=sys.stderr)
            return None
        
        # Clean up the table
        # Remove any rows where all values are NaN
        balance_sheet = balance_sheet.dropna(how='all')
        
        # Try to find the header row containing the dates
        header_row = None
        for idx, row in balance_sheet.iterrows():
            row_text = ' '.join(row.astype(str))
            if re.search(r'\b\d{4}\b', row_text):
                header_row = idx
                break
        
        if header_row is not None:
            # Set the header and skip rows above it
            balance_sheet.columns = balance_sheet.iloc[header_row]
            balance_sheet = balance_sheet.iloc[header_row + 1:]
        
        # Reset index after dropping rows
        balance_sheet = balance_sheet.reset_index(drop=True)
        
        # Clean up column names and replace NaN column names with numbered columns
        balance_sheet.columns = [
            f'col_{i}' if pd.isna(col) or str(col).strip() == '' else str(col).strip()
            for i, col in enumerate(balance_sheet.columns)
        ]
        
        # Clean numeric values in all columns except the first (description)
        numeric_cols = balance_sheet.columns[1:]
        for col in numeric_cols:
            balance_sheet[col] = balance_sheet[col].apply(clean_numeric_value)
        
        # Keep only rows with at least one numeric value
        has_numeric = balance_sheet[numeric_cols].notna().any(axis=1)
        balance_sheet = balance_sheet[has_numeric].copy()
        
        return balance_sheet
    
    except Exception as e:
        print(f"Error extracting balance sheet from {pdf_path}: {e}", file=sys.stderr)
        return None

def process_pdfs(pdf_paths: List[str]) -> pd.DataFrame:
    """
    Process multiple PDFs and combine their balance sheet data.
    Includes validation and cleaning of the extracted data.
    """
    all_data = []
    
    for pdf_path in pdf_paths:
        date = extract_date_from_pdf(pdf_path)
        if not date:
            print(f"Could not extract date from {pdf_path}", file=sys.stderr)
            continue
            
        df = extract_balance_sheet(pdf_path)
        if df is not None:
            # Validate basic balance sheet structure
            if not validate_balance_sheet_structure(df):
                print(f"Invalid balance sheet structure in {pdf_path}", file=sys.stderr)
                continue
                
            # Clean and validate the data
            df = clean_and_validate_data(df)
            if df is not None and not df.empty:
                df['Statement_Date'] = date
                df['Source_File'] = os.path.basename(pdf_path)
                all_data.append(df)
            else:
                print(f"No valid data after cleaning in {pdf_path}", file=sys.stderr)
    
    if not all_data:
        return None
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Additional cleaning on combined data
    # Remove rows that are likely subtotals or section headers
    combined_df = combined_df[
        ~combined_df.iloc[:, 0].str.contains(
            'total|subtotal|section|summary',
            case=False, na=False
        )
    ]
    
    # Sort by date and description
    combined_df = combined_df.sort_values(
        ['Statement_Date', combined_df.columns[0]],
        ascending=[False, True]
    )
    
    # Ensure consistent formatting of description column
    combined_df.iloc[:, 0] = combined_df.iloc[:, 0].str.strip().str.title()
    
    # Drop duplicate rows based on description and date
    combined_df = combined_df.drop_duplicates(
        subset=[combined_df.columns[0], 'Statement_Date'],
        keep='first'
    )
    
    return combined_df

def main():
    parser = argparse.ArgumentParser(
        description='Download financial statement PDFs and extract balance sheet data'
    )
    parser.add_argument(
        'urls',
        nargs='+',
        help='One or more URLs to financial statement PDFs'
    )
    parser.add_argument(
        '--output',
        '-o',
        required=True,
        help='Output CSV file path'
    )
    parser.add_argument(
        '--tmp-dir',
        default='/tmp',
        help='Temporary directory for downloaded PDFs (default: /tmp)'
    )
    
    args = parser.parse_args()
    
    # Download PDFs
    downloaded_files = download_pdfs(args.urls, args.tmp_dir)
    
    if not downloaded_files:
        print("No PDFs were successfully downloaded.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Successfully downloaded {len(downloaded_files)} PDFs")
    
    # Process the PDFs and extract balance sheet data
    combined_data = process_pdfs(downloaded_files)
    
    if combined_data is None:
        print("No balance sheet data could be extracted from the PDFs.", file=sys.stderr)
        sys.exit(1)
    
    # Format numeric columns for CSV output
    def format_numeric_value(value):
        if pd.isna(value):
            return ''
        try:
            # Format large numbers with commas and 2 decimal places
            return f"{float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)

    # Create a copy for CSV output to avoid modifying the original data
    output_data = combined_data.copy()
    
    # Format numeric columns (all except description and metadata columns)
    numeric_cols = [col for col in output_data.columns 
                   if col not in ['Statement_Date', 'Source_File'] 
                   and col != output_data.columns[0]]
    
    for col in numeric_cols:
        output_data[col] = output_data[col].apply(format_numeric_value)

    # Ensure the directory exists
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    # Save to CSV with proper formatting
    try:
        output_data.to_csv(args.output, index=False, quoting=1)
        print(f"Successfully saved balance sheet data to {args.output}")
        
        # Print summary statistics
        print("\nSummary of extracted data:")
        print(f"Total number of rows: {len(output_data)}")
        print(f"Date range: {output_data['Statement_Date'].min()} to {output_data['Statement_Date'].max()}")
        print(f"Number of statements processed: {output_data['Source_File'].nunique()}")
        
    except Exception as e:
        print(f"Error saving to CSV: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()