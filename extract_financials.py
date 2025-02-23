#!/usr/bin/env python3

import argparse
import os
import re
import requests
from urllib.parse import urlparse
from pathlib import Path
import PyPDF2
import camelot
import pandas as pd
from typing import Optional, Tuple, List, Dict
import numpy as np

def download_pdf(url: str, output_dir: str = '/tmp') -> str:
    """
    Download a PDF from a URL and save it to the specified directory.
    
    Args:
        url: The URL of the PDF to download
        output_dir: Directory to save the PDF (defaults to /tmp)
        
    Returns:
        str: Path to the downloaded PDF file
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Extract filename from URL or use a default
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename.endswith('.pdf'):
        filename = 'downloaded.pdf'
    
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    return output_path

def find_balance_sheet_page(pdf_path: str) -> Optional[Tuple[int, str]]:
    """
    Find the page containing the consolidated balance sheets in the PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Tuple of (page number, quarter/year) if found, None otherwise
    """
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text().lower()
            
            # Check if this is the actual balance sheet page by looking for typical balance sheet items
            if ('condensed consolidated balance sheets' in text and
                any(item in text for item in [
                    'cash and cash equivalents',
                    'total assets',
                    'total liabilities',
                    "stockholders' equity"
                ])):
                # Extract fiscal quarter/year information from filename
                filename = os.path.basename(pdf_path).lower()
                quarter_match = re.search(r'q([1-4])', filename)
                year_match = re.search(r'fy(\d{2})', filename)
                
                if quarter_match and year_match:
                    fiscal_period = f"Q{quarter_match.group(1)} FY20{year_match.group(1)}"
                else:
                    # Try to extract from text
                    date_pattern = r'(january|april|july|october)\s+\d{1,2},\s+\d{4}'
                    date_match = re.search(date_pattern, text)
                    if date_match:
                        month_to_quarter = {
                            'january': 'Q4',
                            'april': 'Q1',
                            'july': 'Q2',
                            'october': 'Q3'
                        }
                        month = date_match.group(1)
                        fiscal_period = f"{month_to_quarter[month]} FY2025"
                    else:
                        fiscal_period = "Unknown"
                
                return page_num, fiscal_period
                
    return None

def extract_balance_sheet_page(pdf_path: str, page_num: int) -> str:
    """
    Extract the balance sheet page to a new PDF file.
    
    Args:
        pdf_path: Path to the source PDF file
        page_num: Page number to extract
        
    Returns:
        str: Path to the extracted page PDF
    """
    output_path = pdf_path.replace('.pdf', f'_balance_sheet.pdf')
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Add the balance sheet page to the new PDF
        pdf_writer.add_page(pdf_reader.pages[page_num])
        
        # Save the new PDF
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)
    
    return output_path

def extract_tables(pdf_path: str) -> List[pd.DataFrame]:
    """
    Extract tables from the PDF using Camelot.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of pandas DataFrames containing the extracted tables
    """
    # Try different table areas and flavors
    table_areas = [
        [50, 50, 750, 550],  # Middle of page
        [100, 100, 700, 500],  # More restricted area
        [150, 150, 650, 450]  # Even more restricted area
    ]
    
    tables = []
    
    for area in table_areas:
        # Try both stream and lattice flavors with different settings
        tables_stream = camelot.read_pdf(
            pdf_path, 
            pages='1', 
            flavor='stream',
            table_areas=[','.join(map(str, area))],
            strip_text='\n',
            edge_tol=500
        )
        
        tables_lattice = camelot.read_pdf(
            pdf_path, 
            pages='1', 
            flavor='lattice',
            table_areas=[','.join(map(str, area))]
        )
        
        # Add tables from both methods, filtering out empty ones
        for table_list in [tables_stream, tables_lattice]:
            for table in table_list:
                df = table.df
                if not df.empty and len(df.columns) >= 2:  # At least line item and amount columns
                    # Clean up the DataFrame
                    df = df.replace('', np.nan).dropna(how='all')
                    if not df.empty:
                        tables.append(df)
    
    return tables

def clean_monetary_value(value: str) -> float:
    """
    Clean and convert monetary value strings to float.
    
    Args:
        value: String representation of a monetary value
        
    Returns:
        float: Cleaned monetary value
    """
    if pd.isna(value) or not value or value == '—':
        raise ValueError("Empty or null monetary value")
        
    if isinstance(value, (int, float)):
        return float(value)
        
    # Remove currency symbols, commas, spaces, and handle parentheses for negative values
    cleaned = value.replace('$', '').replace(',', '').replace(' ', '')
    
    # Handle parentheses for negative values
    if '(' in cleaned and ')' in cleaned:
        cleaned = '-' + cleaned.replace('(', '').replace(')', '')
    
    # Handle 'million' and 'billion' indicators
    if 'million' in cleaned.lower():
        cleaned = cleaned.lower().replace('million', '').strip()
        multiplier = 1_000_000
    elif 'billion' in cleaned.lower():
        cleaned = cleaned.lower().replace('billion', '').strip()
        multiplier = 1_000_000_000
    else:
        multiplier = 1
    
    try:
        return float(cleaned) * multiplier
    except ValueError:
        raise ValueError(f"Invalid monetary value: {value}")

def identify_category(line_item: str) -> Optional[str]:
    """
    Identify if a line item is a category header.
    
    Args:
        line_item: The line item text
        
    Returns:
        str or None: Category name if it's a category header, None otherwise
    """
    # Clean up line item
    line_item = re.sub(r'^\d+,\s*', '', line_item)  # Remove leading numbers
    line_item = re.sub(r'^\d+\s+', '', line_item)   # Remove leading numbers with spaces
    line_item = re.sub(r',\d+$', '', line_item)     # Remove trailing numbers
    line_item = line_item.strip(':').strip()
    
    # Skip if line item is just a number
    if re.match(r'^\d+$', line_item):
        return None
    
    line_lower = line_item.lower()
    
    # Define category mappings
    category_mappings = {
        'assets': 'Assets',
        'current assets': 'Current Assets',
        'non-current assets': 'Non-current Assets',
        'liabilities': 'Liabilities',
        'current liabilities': 'Current Liabilities',
        'non-current liabilities': 'Non-current Liabilities',
        "stockholders' equity": "Stockholders' Equity",
        'operating lease': 'Operating Lease Assets',
        'goodwill': 'Intangible Assets',
        'intangible': 'Intangible Assets',
        'deferred': 'Deferred Items',
        'convertible': 'Debt',
        'notes': 'Debt'
    }
    
    # Skip if line item contains typical non-category terms
    if any(term in line_lower for term in ['net', 'total', 'accumulated']):
        return None
    
    # Check for category indicators
    if (line_item.isupper() or
        line_lower.endswith(':') or
        line_lower.endswith('assets') or
        line_lower.endswith('liabilities') or
        (len(line_item.split()) <= 3 and any(word[0].isupper() for word in line_item.split()))):
        
        # Try to map to a known category
        for key, category in category_mappings.items():
            if key in line_lower:
                return category
        
        # If no mapping found but it looks like a category, use Other
        return 'Other'
    
    return None

def is_total_line(line_item: str, amount: float, previous_amounts: List[float]) -> bool:
    """
    Determine if a line item is a total by checking both the text and values.
    
    Args:
        line_item: The line item text
        amount: The amount for this line
        previous_amounts: List of previous amounts in the same category
        
    Returns:
        bool: True if this is a total line, False otherwise
    """
    # Check text indicators
    text_indicators = line_item.lower().startswith('total') or 'total' in line_item.lower()
    
    # Check if amount approximately equals sum of previous amounts (within 1% margin)
    if previous_amounts:
        sum_previous = sum(previous_amounts)
        if abs(sum_previous - amount) <= abs(sum_previous * 0.01):
            return True
    
    return text_indicators

def validate_data_consistency(df: pd.DataFrame) -> None:
    """
    Validate data consistency and raise errors for invalid data.
    
    Args:
        df: DataFrame containing the processed data
        
    Raises:
        ValueError: If data consistency checks fail
    """
    # Check for missing categories
    if df['category'].isna().any():
        raise ValueError("Found line items with missing categories")
    
    # Check for invalid amounts
    if df['amount'].isna().any():
        raise ValueError("Found line items with missing amounts")
    
    # Verify total assets equals total liabilities plus equity
    try:
        total_assets = df[
            (df['line_item'].str.lower().str.contains('total assets')) &
            (df['is_total'] == True)
        ]['amount'].iloc[0]
        
        total_liab_equity = df[
            (df['line_item'].str.lower().str.contains("total liabilities and stockholders' equity")) &
            (df['is_total'] == True)
        ]['amount'].iloc[0]
        
        if not np.isclose(total_assets, total_liab_equity, rtol=0.01):
            raise ValueError(
                f"Balance sheet doesn't balance: Total assets ({total_assets}) != "
                f"Total liabilities and equity ({total_liab_equity})"
            )
    except IndexError:
        print("Warning: Could not validate total assets against total liabilities and equity")

def process_balance_sheet_data(tables: List[pd.DataFrame], fiscal_quarter: str) -> pd.DataFrame:
    """
    Process the extracted tables into a structured format.
    
    Args:
        tables: List of pandas DataFrames containing the raw table data
        fiscal_quarter: The fiscal quarter identifier (e.g., 'Q1 FY2025')
        
    Returns:
        pandas DataFrame with processed data
    """
    if not tables:
        raise ValueError("No tables found in the PDF")
    
    # Find the table with the most rows (likely the main balance sheet)
    df = max(tables, key=len)
    
    # Clean up the data
    df = df.replace('', np.nan).dropna(how='all')
    
    # Initialize lists to store processed data
    processed_data = []
    current_category = 'Assets'  # Default initial category
    category_amounts = []
    
    # Process each row
    for idx, row in df.iterrows():
        # Get all non-null values from the row
        values = [str(val).strip() for val in row if pd.notna(val) and str(val).strip()]
        if not values:
            continue
            
        line_item = values[0]
        
        # Skip header rows and empty rows
        if any(header in line_item.lower() for header in ['january', 'october', 'july', 'april']):
            continue
            
        # Clean up line item
        line_item = line_item.strip()
        if not line_item or line_item.isspace() or line_item == '—':
            continue
            
        # Check if this is a category header
        category = identify_category(line_item)
        if category:
            current_category = category
            category_amounts = []
            continue
            
        try:
            # Look for monetary values in the row
            amount = None
            for val in values[1:]:  # Skip the line item
                try:
                    amount = clean_monetary_value(val)
                    break
                except ValueError:
                    continue
                    
            if amount is None:
                continue
                
            # Clean up line item
            line_item = re.sub(r'^\d+,\s*', '', line_item)  # Remove leading numbers
            line_item = re.sub(r'^\d+\s+', '', line_item)   # Remove leading numbers with spaces
            line_item = re.sub(r',\d+$', '', line_item)     # Remove trailing numbers
            line_item = line_item.strip()
            
            # Skip if line item is just a number
            if re.match(r'^\d+$', line_item):
                continue
                
            # Determine if this is a total row
            is_total = is_total_line(line_item, amount, category_amounts)
            
            if not is_total:
                category_amounts.append(amount)
            
            processed_data.append({
                'fiscal_quarter': fiscal_quarter,
                'category': current_category,
                'line_item': line_item,
                'amount': amount,
                'is_total': is_total
            })
            
        except ValueError as e:
            print(f"Warning: Skipping row due to invalid data: {e}")
            continue
    
    result_df = pd.DataFrame(processed_data)
    
    # Validate the processed data
    validate_data_consistency(result_df)
    
    return result_df

def save_to_csv(df: pd.DataFrame, output_path: str):
    """
    Save the processed data to a CSV file.
    
    Args:
        df: pandas DataFrame containing the processed data
        output_path: Path where the CSV should be saved
    """
    df.to_csv(output_path, index=False)

def main():
    parser = argparse.ArgumentParser(description='Extract financial data from Snowflake quarterly reports')
    parser.add_argument('url', help='URL of the PDF financial statement')
    parser.add_argument('--output', required=True, help='Path to output CSV file')
    
    args = parser.parse_args()
    
    try:
        # Download the PDF
        pdf_path = download_pdf(args.url)
        print(f"Downloaded PDF to: {pdf_path}")
        
        # Find the balance sheet page
        result = find_balance_sheet_page(pdf_path)
        if not result:
            print("Could not find consolidated balance sheets in the PDF")
            return 1
            
        page_num, fiscal_period = result
        print(f"Found balance sheet on page {page_num + 1} for period {fiscal_period}")
        
        # Extract the balance sheet page to a new PDF
        extracted_pdf = extract_balance_sheet_page(pdf_path, page_num)
        print(f"Extracted balance sheet page to: {extracted_pdf}")
        
        # Extract tables from the PDF
        tables = extract_tables(extracted_pdf)
        print(f"Extracted {len(tables)} tables from the PDF")
        
        # Process the balance sheet data
        df = process_balance_sheet_data(tables, fiscal_period)
        print(f"Processed {len(df)} rows of balance sheet data")
        
        # Save to CSV
        save_to_csv(df, args.output)
        print(f"Saved processed data to: {args.output}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return 1
    except ValueError as e:
        print(f"Error processing data: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())