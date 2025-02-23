#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path
from typing import List
import urllib.request
import tabula
import PyPDF2
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime
import re

def identify_statement_date(pdf_path: str) -> str:
    """
    Extract the statement date from the PDF filename or content.
    Returns the date in YYYY-MM-DD format.
    """
    filename = os.path.basename(pdf_path).lower()
    
    # Try to identify fiscal year and quarter
    fy_match = re.search(r'fy(\d{2})', filename)
    q_match = re.search(r'q(\d)', filename)
    
    if fy_match and q_match:
        fy = int('20' + fy_match.group(1))
        quarter = int(q_match.group(1))
        # Map fiscal quarters to calendar quarters (Snowflake's fiscal year starts in February)
        month = {1: '04', 2: '07', 3: '10', 4: '01'}[quarter]
        year = fy if quarter != 4 else fy - 1
        return f"{year}-{month}-30"
    
    # For annual reports (10-K)
    if '10k' in filename or '10-k' in filename:
        if fy_match:
            fy = int('20' + fy_match.group(1))
            return f"{fy-1}-01-31"
    
    return None

def extract_balance_sheet(pdf_path: str) -> pd.DataFrame:
    """
    Extract the consolidated balance sheet from a PDF file.
    Returns a DataFrame with the balance sheet data.
    """
    # Try different table extraction methods
    extraction_methods = [
        {'lattice': True, 'guess': False},
        {'lattice': False, 'guess': True},
        {'lattice': True, 'guess': True},
    ]
    
    # Keywords to identify balance sheet tables
    balance_sheet_keywords = [
        'consolidated balance',
        'balance sheets',
        'consolidated statements of financial position',
        'statements of financial position'
    ]
    
    # Keywords to identify balance sheet content
    content_keywords = [
        'current assets',
        'total assets',
        'cash and cash equivalents',
        'accounts receivable',
        'total liabilities',
        'stockholders equity'
    ]
    
    best_table = None
    best_score = 0
    
    # First try to find the page with the balance sheet
    target_page = None
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        print(f"PDF has {len(pdf.pages)} pages")
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text().lower()
            print(f"Scanning page {page_num} for balance sheet...")
            
            # Check for balance sheet title
            title_match = any(keyword in text for keyword in balance_sheet_keywords)
            if title_match:
                print(f"Found balance sheet title on page {page_num}")
                
                # Check for content keywords
                content_matches = sum(1 for keyword in content_keywords if keyword in text)
                if content_matches >= 2:  # At least 2 content keywords
                    target_page = page_num
                    print(f"Found balance sheet content on page {page_num} ({content_matches} matches)")
                    break
    
    if target_page:
        pages_to_check = [target_page]
    else:
        # If no target page found, check first 10 pages
        pages_to_check = list(range(1, min(len(pdf.pages) + 1, 11)))
        print(f"No specific balance sheet page found, checking pages {pages_to_check}")
    
    for method in extraction_methods:
        try:
            print(f"\nTrying extraction method: {method}")
            # Extract tables from the target pages
            tables = tabula.read_pdf(
                pdf_path,
                pages=pages_to_check,
                multiple_tables=True,
                pandas_options={'header': None},
                **method
            )
            print(f"Found {len(tables)} tables")
            
            # Find the balance sheet table
            for table_idx, table in enumerate(tables):
                print(f"\nAnalyzing table {table_idx + 1}:")
                print(f"Shape: {table.shape}")
                
                if table.empty or table.shape[1] < 2:
                    print("Skipping: Empty or single-column table")
                    continue
                
                # Clean up the table
                table = table.dropna(how='all').dropna(axis=1, how='all')
                if table.empty or table.shape[1] < 2:
                    print("Skipping: Table is empty after cleaning")
                    continue
                
                print(f"Cleaned shape: {table.shape}")
                
                # Convert all values to string and join them
                table_text = ' '.join(table.astype(str).values.flatten()).lower()
                
                # Calculate match score
                score = 0
                
                # Check for balance sheet title
                title_match = any(keyword in table_text for keyword in balance_sheet_keywords)
                if title_match:
                    score += 5
                    print("Found balance sheet title (+5 points)")
                
                # Check for balance sheet content
                content_matches = sum(1 for keyword in content_keywords if keyword in table_text)
                if content_matches > 0:
                    score += content_matches
                    print(f"Found {content_matches} content keywords (+{content_matches} points)")
                
                # Check for numeric content
                numeric_count = 0
                for val in table.values.flatten():
                    try:
                        val_str = str(val).strip().replace(',', '').replace('$', '')
                        if re.match(r'^-?\d+\.?\d*$', val_str):
                            numeric_count += 1
                    except:
                        continue
                
                numeric_score = min(numeric_count / 10, 3)
                if numeric_score > 0:
                    score += numeric_score
                    print(f"Found {numeric_count} numeric values (+{numeric_score:.1f} points)")
                
                print(f"Total score: {score}")
                
                # Update best table if this one has a higher score
                if score > best_score:
                    print("This is the best table so far")
                    best_score = score
                    best_table = table
            
        except Exception as e:
            print(f"Warning: Table extraction method failed: {str(e)}")
            continue
    
    if best_table is not None and best_score >= 3:
        print(f"\nSelected best table with score {best_score}")
        
        # Clean up the table
        # Find the header row (usually contains date information)
        header_idx = None
        date_terms = ['january', 'february', 'march', 'april', 'may', 'june', 
                     'july', 'august', 'september', 'october', 'november', 'december']
        
        for idx, row in best_table.iterrows():
            row_text = ' '.join(row.astype(str)).lower()
            if any(term in row_text for term in date_terms):
                if re.search(r'\b20\d{2}\b', row_text):
                    header_idx = idx
                    break
        
        if header_idx is not None:
            # Set the header and drop the rows above it
            best_table.columns = best_table.iloc[header_idx]
            best_table = best_table.iloc[header_idx + 1:].reset_index(drop=True)
        
        # Clean up column names
        # First column is always the line item name
        best_table.columns = ['Line Item'] + [f'Value_{i+1}' for i in range(best_table.shape[1]-1)]
        
        # Remove rows that don't look like balance sheet items
        rows_to_keep = []
        for idx, row in best_table.iterrows():
            line_item = str(row.iloc[0]).strip().lower()
            if not line_item or pd.isna(line_item):
                continue
            
            if re.search(r'^\d+$|^table\s+of\s+contents$|^notes?$|^page$|^in\s+thousands$|^consolidated\s+statements?\s+of', line_item):
                continue
            
            # Check if there are any valid numeric values
            has_numbers = False
            for val in row.iloc[1:]:
                try:
                    val_str = str(val).strip().replace(',', '').replace('$', '')
                    if re.match(r'^-?\d+\.?\d*$', val_str):
                        has_numbers = True
                        break
                except:
                    continue
            
            if has_numbers:
                rows_to_keep.append(idx)
        
        best_table = best_table.iloc[rows_to_keep].reset_index(drop=True)
        return best_table
    
    raise ValueError(f"Could not find consolidated balance sheet in {pdf_path}")

def standardize_line_item(item: str) -> str:
    """
    Standardize balance sheet line item names.
    """
    item = str(item).lower().strip()
    
    # Common variations mapping
    mappings = {
        'cash and cash equivalents': ['cash and cash equiv', 'cash & cash equivalents', 'cash & cash equiv'],
        'accounts receivable': ['trade receivables', 'net accounts receivable', 'accounts receivable, net'],
        'total current assets': ['current assets total', 'total curr assets'],
        'total assets': ['assets total', 'total consolidated assets'],
        'accounts payable': ['trade payables', 'accounts payable and accrued expenses'],
        'total current liabilities': ['current liabilities total', 'total curr liabilities'],
        'total liabilities': ['liabilities total', 'total consolidated liabilities'],
        'stockholders equity': ["stockholders' equity", 'total stockholders equity', 'shareholders equity'],
    }
    
    # Find and replace variations
    for standard, variations in mappings.items():
        if item in variations or item == standard:
            return standard
    
    return item

def convert_value_to_float(value: str) -> float:
    """
    Convert a string value to float, handling various formats.
    """
    if pd.isna(value) or str(value).strip() in ['', 'nan', 'None']:
        return None
        
    value = str(value).strip()
    
    # Remove currency symbols and commas
    value = value.replace('$', '').replace(',', '')
    
    # Handle parentheses (negative numbers)
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    
    # Handle percentage values
    if '%' in value:
        value = value.replace('%', '')
        try:
            return float(value) / 100
        except ValueError:
            return None
    
    try:
        return float(value)
    except ValueError:
        return None

def validate_balance_sheet(df: pd.DataFrame) -> bool:
    """
    Perform validation checks on the balance sheet data.
    Returns True if all checks pass, False otherwise.
    """
    try:
        # Check if essential columns exist
        essential_items = ['total assets', 'total liabilities', "stockholders equity"]
        found_items = df.iloc[:, 0].astype(str).str.lower()
        
        # Map variations of essential items
        item_variations = {
            'total assets': ['total assets', 'assets total', 'total consolidated assets'],
            'total liabilities': ['total liabilities', 'liabilities total', 'total consolidated liabilities'],
            'stockholders equity': ["stockholders' equity", 'total stockholders equity', 'shareholders equity', 
                                  "total stockholders' equity", 'total equity']
        }
        
        # Check for essential items using variations
        missing_items = []
        for item, variations in item_variations.items():
            if not found_items.str.contains('|'.join(variations), regex=True).any():
                missing_items.append(item)
        
        if missing_items:
            print(f"Warning: Missing essential line items: {', '.join(missing_items)}")
            return True  # Continue even if some items are missing
        
        # Check for numeric values in data columns
        numeric_cols = []
        for col in df.columns[1:]:
            if pd.to_numeric(df[col], errors='coerce').notna().any():
                numeric_cols.append(col)
        
        if not numeric_cols:
            print("Warning: No columns with valid numeric values found")
            return False
        
        # Verify basic accounting equation: Assets = Liabilities + Equity
        for col in numeric_cols:
            try:
                # Find total assets
                assets_mask = found_items.str.contains('|'.join(item_variations['total assets']), regex=True)
                total_assets = pd.to_numeric(df[assets_mask][col].iloc[0], errors='coerce')
                
                # Find total liabilities
                liabilities_mask = found_items.str.contains('|'.join(item_variations['total liabilities']), regex=True)
                total_liabilities = pd.to_numeric(df[liabilities_mask][col].iloc[0], errors='coerce')
                
                # Find total equity
                equity_mask = found_items.str.contains('|'.join(item_variations['stockholders equity']), regex=True)
                total_equity = pd.to_numeric(df[equity_mask][col].iloc[0], errors='coerce')
                
                # Skip validation if any value is missing
                if pd.isna(total_assets) or pd.isna(total_liabilities) or pd.isna(total_equity):
                    print(f"Warning: Missing values for accounting equation in column {col}")
                    continue
                
                # Check accounting equation with 1% tolerance
                if abs((total_assets - (total_liabilities + total_equity)) / total_assets) > 0.01:
                    print(f"Warning: Assets != Liabilities + Equity for column {col}")
                    continue
                
            except (IndexError, ValueError, ZeroDivisionError) as e:
                print(f"Warning: Could not verify accounting equation for column {col}: {str(e)}")
                continue
        
        return True
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return True  # Continue despite validation errors

def clean_balance_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize the extracted balance sheet data.
    """
    try:
        # Clean up line items and convert numeric values
        for idx, row in df.iterrows():
            # Clean up line item
            df.iloc[idx, 0] = standardize_line_item(str(row.iloc[0]).strip())
            
            # Convert numeric values
            for col_idx in range(1, len(df.columns)):
                df.iloc[idx, col_idx] = convert_value_to_float(row.iloc[col_idx])
        
        # Drop rows where all numeric columns are None
        numeric_cols = df.columns[1:]
        df = df.dropna(subset=numeric_cols, how='all')
        
        # Validate the cleaned data
        if not validate_balance_sheet(df):
            print("Warning: Balance sheet validation failed")
        
        return df
        
    except Exception as e:
        print(f"Error cleaning balance sheet: {str(e)}")
        return pd.DataFrame()

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Extract consolidated balance sheets from Snowflake financial statements'
    )
    parser.add_argument(
        'urls',
        nargs='+',
        help='URLs of the PDF financial statements'
    )
    parser.add_argument(
        '--output',
        required=True,
        type=str,
        help='Path to the output CSV file'
    )
    return parser.parse_args()

def download_pdf(url: str, tmp_dir: str = '/tmp') -> str:
    """
    Download a PDF from a URL and save it to the tmp directory.
    Returns the path to the downloaded file.
    """
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    
    output_path = os.path.join(tmp_dir, filename)
    
    try:
        urllib.request.urlretrieve(url, output_path)
        # Verify the downloaded file is a valid PDF
        with open(output_path, 'rb') as f:
            PyPDF2.PdfReader(f)
        return output_path
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}", file=sys.stderr)
        raise

def download_pdfs(urls: List[str], tmp_dir: str = '/tmp') -> List[str]:
    """
    Download multiple PDFs and return a list of their local file paths.
    """
    pdf_paths = []
    for url in urls:
        try:
            pdf_path = download_pdf(url, tmp_dir)
            pdf_paths.append(pdf_path)
            print(f"Successfully downloaded: {url} -> {pdf_path}")
        except Exception as e:
            print(f"Skipping {url} due to error: {str(e)}", file=sys.stderr)
    
    if not pdf_paths:
        raise RuntimeError("No PDFs were successfully downloaded")
    
    return pdf_paths

def process_pdf(pdf_path: str) -> tuple[pd.DataFrame, str]:
    """
    Process a single PDF file and return its balance sheet data and statement date.
    """
    print(f"Processing {pdf_path}...")
    
    try:
        # Extract the statement date
        statement_date = identify_statement_date(pdf_path)
        if not statement_date:
            print(f"Warning: Could not identify statement date for {pdf_path}")
        
        # Extract and clean the balance sheet
        balance_sheet = extract_balance_sheet(pdf_path)
        if balance_sheet is None or balance_sheet.empty:
            print(f"Warning: No balance sheet data found in {pdf_path}")
            return pd.DataFrame(), statement_date
        
        cleaned_data = clean_balance_sheet(balance_sheet)
        if cleaned_data.empty:
            print(f"Warning: Failed to clean balance sheet data from {pdf_path}")
            return pd.DataFrame(), statement_date
        
        return cleaned_data, statement_date
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return pd.DataFrame(), None

def main():
    args = parse_arguments()
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Process one URL at a time
        all_data = []
        successful_extractions = 0
        
        for url in args.urls:
            print(f"\nProcessing URL: {url}")
            
            try:
                # Download PDF
                pdf_path = download_pdf(url)
                print(f"Successfully downloaded to: {pdf_path}")
                
                # Process the PDF
                df, statement_date = process_pdf(pdf_path)
                
                if not df.empty:
                    # Add metadata columns
                    df.insert(0, 'Statement Date', statement_date if statement_date else 'Unknown')
                    df.insert(1, 'Source File', os.path.basename(pdf_path))
                    
                    # Ensure column names are unique
                    cols = list(df.columns)
                    for i in range(len(cols)):
                        count = 1
                        while cols.count(cols[i]) > 1:
                            cols[i] = f"{cols[i]}_{count}"
                            count += 1
                    df.columns = cols
                    
                    print("\nExtracted data shape:", df.shape)
                    print("Columns:", df.columns.tolist())
                    print("\nFirst few rows:")
                    print(df.head())
                    
                    all_data.append(df)
                    successful_extractions += 1
                    print("\nSuccessfully extracted data")
                
            except Exception as e:
                print(f"\nError processing {url}: {str(e)}")
                continue
        
        if successful_extractions == 0:
            raise RuntimeError("No data was successfully extracted from any of the PDFs")
        
        # Combine all the data
        if len(all_data) == 1:
            combined_data = all_data[0]
        else:
            print("\nCombining data from multiple files...")
            
            # Standardize column names
            for df in all_data:
                # Rename numeric columns to match their position
                numeric_cols = df.columns[3:]  # Skip Statement Date, Source File, Line Item
                df.columns = ['Statement Date', 'Source File', 'Line Item'] + [f'Value_{i+1}' for i in range(len(numeric_cols))]
            
            # Find the maximum number of value columns
            max_values = max(len(df.columns) - 3 for df in all_data)  # -3 for Statement Date, Source File, Line Item
            
            # Ensure all DataFrames have the same number of columns
            for df in all_data:
                current_values = len(df.columns) - 3
                if current_values < max_values:
                    for i in range(current_values + 1, max_values + 1):
                        df[f'Value_{i}'] = None
            
            # Combine the data
            combined_data = pd.concat(all_data, ignore_index=True)
            
            # Sort by Statement Date and Line Item
            combined_data = combined_data.sort_values(['Statement Date', 'Line Item'])
        
        # Save to CSV
        combined_data.to_csv(args.output, index=False)
        print(f"\nSummary:")
        print(f"- Total PDFs processed: {len(args.urls)}")
        print(f"- Successful extractions: {successful_extractions}")
        print(f"- Failed extractions: {len(args.urls) - successful_extractions}")
        print(f"- Output saved to: {args.output}")
        print("\nFinal data shape:", combined_data.shape)
        print("Final columns:", combined_data.columns.tolist())
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()