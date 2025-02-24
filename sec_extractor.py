#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import requests
from bs4 import BeautifulSoup, Tag
import logging
import pandas as pd
import re

def setup_argparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Extract tables from Microsoft 10Q SEC filing and save as CSV files'
    )
    parser.add_argument(
        '--url',
        type=str,
        required=True,
        help='URL of the Microsoft 10Q SEC filing'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        required=True,
        help='Output directory path for saving CSV files'
    )
    return parser.parse_args()

def validate_url(url: str) -> bool:
    """Validate if the provided URL is a Microsoft GCS web URL."""
    return url.startswith('https://microsoft.gcs-web.com/')

def ensure_output_directory(directory: str) -> Path:
    """Create output directory if it doesn't exist and return Path object."""
    output_path = Path(directory)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def fetch_url_content(url: str) -> BeautifulSoup:
    """
    Fetch content from URL and return BeautifulSoup object.
    
    Args:
        url: The URL to fetch content from
        
    Returns:
        BeautifulSoup object containing the parsed HTML
        
    Raises:
        requests.RequestException: If there's an error fetching the URL
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        logging.error(f"Failed to fetch URL content: {e}")
        raise

def find_table_by_header(soup: BeautifulSoup, header_text: str, proximity: int = 2) -> Optional[Tag]:
    """
    Find a table that appears after text matching the header_text pattern.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        header_text: Text pattern to search for
        proximity: Number of elements to look ahead for the table
        
    Returns:
        BeautifulSoup Tag object containing the table if found, None otherwise
    """
    header_pattern = re.compile(header_text, re.IGNORECASE)
    
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div']):
        if header_pattern.search(element.get_text(strip=True)):
            current = element
            for _ in range(proximity):
                if not current:
                    break
                current = current.find_next()
                if current and current.name == 'table':
                    return current
    return None

def clean_number(text: str) -> Optional[float]:
    """
    Convert a string containing a number (possibly with parentheses, $ signs, etc.) to a float.
    Handles negative numbers in parentheses and removes currency symbols.
    
    Args:
        text: String containing a number
        
    Returns:
        Float value if conversion successful, None otherwise
    """
    try:
        # Remove $ and any other currency symbols, commas, and whitespace
        text = text.replace('$', '').replace(',', '').strip()
        
        # Handle negative numbers in parentheses
        if text.startswith('(') and text.endswith(')'):
            text = '-' + text[1:-1]
            
        # Handle empty or non-numeric strings
        if not text or text.lower() in ['na', 'n/a', '-']:
            return None
            
        return float(text)
    except ValueError:
        return None

def clean_header(header: str) -> str:
    """
    Clean and standardize table headers.
    
    Args:
        header: Raw header text
        
    Returns:
        Cleaned header text
    """
    # Remove newlines and excessive whitespace
    header = ' '.join(header.split())
    
    # Remove footnote references
    header = re.sub(r'\([0-9]+\)$', '', header)
    
    # Standardize common terms
    replacements = {
        'Three Months Ended': '3M',
        'Six Months Ended': '6M',
        'Nine Months Ended': '9M',
        'Twelve Months Ended': '12M',
        'Year Ended': 'YE',
    }
    for old, new in replacements.items():
        header = header.replace(old, new)
        
    return header.strip()

def clean_table_data(table: Tag) -> pd.DataFrame:
    """
    Convert a BeautifulSoup table tag to a pandas DataFrame with cleaned data.
    
    Args:
        table: BeautifulSoup Tag object containing the table
        
    Returns:
        pandas DataFrame containing the cleaned table data
    """
    rows = []
    headers = []
    
    # Extract and clean headers
    header_row = table.find('tr')
    if header_row:
        headers = [clean_header(cell.get_text(strip=True)) 
                  for cell in header_row.find_all(['th', 'td'])]
        
    # Handle colspan in headers
    for cell in header_row.find_all(['th', 'td']):
        colspan = int(cell.get('colspan', 1))
        if colspan > 1:
            header_text = clean_header(cell.get_text(strip=True))
            headers.extend([f"{header_text} ({i+1})" for i in range(colspan)])
    
    # Extract data rows
    for row in table.find_all('tr')[1:]:
        cells = []
        for cell in row.find_all(['td', 'th']):
            text = cell.get_text(strip=True)
            # Try to convert to number if it looks like a financial value
            if re.search(r'[$()]|\d', text):
                value = clean_number(text)
                cells.append(value if value is not None else text)
            else:
                cells.append(text)
        
        if cells:  # Skip empty rows
            rows.append(cells)
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers if headers else None)
    
    # Clean up the data
    df = df.replace(r'^\s*$', pd.NA, regex=True)  # Replace empty strings with NA
    df = df.dropna(how='all')  # Drop rows that are all NA
    df = df.dropna(axis=1, how='all')  # Drop columns that are all NA
    
    return df

def save_table_to_csv(df: pd.DataFrame, output_path: Path):
    """
    Save a DataFrame to a CSV file with proper formatting for financial data.
    
    Args:
        df: pandas DataFrame to save
        output_path: Path object specifying where to save the CSV
    """
    # Format numeric columns with 2 decimal places
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        df[col] = df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else '')
    
    # Save with UTF-8 encoding and proper quoting
    df.to_csv(output_path, 
              index=False,
              encoding='utf-8',
              quoting=1,  # Quote all non-numeric fields
              na_rep='',  # Empty string for NA values
              float_format='%.2f')

def extract_income_statements(soup: BeautifulSoup) -> Optional[pd.DataFrame]:
    """
    Extract the income statements table from the 10Q report.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        
    Returns:
        pandas DataFrame containing the income statements if found, None otherwise
    """
    table = find_table_by_header(soup, r"INCOME\s+STATEMENTS?")
    if table is None:
        logging.warning("Income statements table not found")
        return None
        
    logging.info("Found income statements table")
    return clean_table_data(table)

def extract_balance_sheets(soup: BeautifulSoup) -> Optional[pd.DataFrame]:
    """
    Extract the balance sheets table from the 10Q report.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        
    Returns:
        pandas DataFrame containing the balance sheets if found, None otherwise
    """
    table = find_table_by_header(soup, r"BALANCE\s+SHEETS?")
    if table is None:
        logging.warning("Balance sheets table not found")
        return None
        
    logging.info("Found balance sheets table")
    return clean_table_data(table)

def extract_cash_flows(soup: BeautifulSoup) -> Optional[pd.DataFrame]:
    """
    Extract the cash flows statements table from the 10Q report.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        
    Returns:
        pandas DataFrame containing the cash flows statements if found, None otherwise
    """
    table = find_table_by_header(soup, r"CASH\s+FLOWS?\s+STATEMENTS?")
    if table is None:
        logging.warning("Cash flows statements table not found")
        return None
        
    logging.info("Found cash flows statements table")
    return clean_table_data(table)

def extract_investments(soup: BeautifulSoup) -> Optional[pd.DataFrame]:
    """
    Extract the investments table from the 10Q report.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        
    Returns:
        pandas DataFrame containing the investments data if found, None otherwise
    """
    table = find_table_by_header(soup, r"INVESTMENTS")
    if table is None:
        logging.warning("Investments table not found")
        return None
        
    logging.info("Found investments table")
    return clean_table_data(table)

def extract_stockholders_equity(soup: BeautifulSoup) -> Optional[pd.DataFrame]:
    """
    Extract the stockholders' equity statements table from the 10Q report.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        
    Returns:
        pandas DataFrame containing the stockholders' equity data if found, None otherwise
    """
    table = find_table_by_header(soup, r"STOCKHOLDERS['']?\s*EQUITY\s+STATEMENTS?")
    if table is None:
        logging.warning("Stockholders' equity statements table not found")
        return None
        
    logging.info("Found stockholders' equity statements table")
    return clean_table_data(table)

def main():
    setup_logging()
    args = setup_argparse()
    
    if not validate_url(args.url):
        logging.error("URL must be from microsoft.gcs-web.com domain")
        sys.exit(1)
    
    try:
        output_path = ensure_output_directory(args.output_dir)
    except Exception as e:
        logging.error(f"Error creating output directory: {e}")
        sys.exit(1)
    
    try:
        logging.info(f"Fetching content from {args.url}")
        soup = fetch_url_content(args.url)
        logging.info("Successfully fetched and parsed URL content")
        
        # Extract and save tables
        income_statements = extract_income_statements(soup)
        balance_sheets = extract_balance_sheets(soup)
        cash_flows = extract_cash_flows(soup)
        investments = extract_investments(soup)
        stockholders_equity = extract_stockholders_equity(soup)
        
        if income_statements is not None:
            save_table_to_csv(income_statements, output_path / 'income_statements.csv')
            logging.info("Successfully saved income statements")
        
        if balance_sheets is not None:
            save_table_to_csv(balance_sheets, output_path / 'balance_sheets.csv')
            logging.info("Successfully saved balance sheets")
            
        if cash_flows is not None:
            save_table_to_csv(cash_flows, output_path / 'cash_flows.csv')
            logging.info("Successfully saved cash flows statements")
            
        if investments is not None:
            save_table_to_csv(investments, output_path / 'investments.csv')
            logging.info("Successfully saved investments table")
            
        if stockholders_equity is not None:
            save_table_to_csv(stockholders_equity, output_path / 'stockholders_equity.csv')
            logging.info("Successfully saved stockholders' equity statements")
        
        return soup, output_path
        
    except Exception as e:
        logging.error(f"Error processing URL: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()