#!/usr/bin/env python3

import argparse
import sys
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import pandas as pd


def fetch_and_parse_html(url: str) -> BeautifulSoup:
    """
    Fetch HTML content from the given URL and return a BeautifulSoup object.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        sys.exit(1)


def extract_balance_sheet(soup: BeautifulSoup) -> pd.DataFrame:
    """
    Extract the Condensed Consolidated Balance Sheets table from the parsed HTML.
    Returns a DataFrame with the required structure.
    """
    # Find the table by looking for the title text
    title_text = "CONDENSED CONSOLIDATED BALANCE SHEETS"
    tables = soup.find_all('table')
    target_table = None
    
    for table in tables:
        # Look for the title in table headers or preceding text
        if table.find_previous(text=lambda x: x and title_text in x.upper()):
            target_table = table
            break
    
    if not target_table:
        print("Error: Could not find the balance sheet table", file=sys.stderr)
        sys.exit(1)

    # Extract headers to identify fiscal quarters
    headers = []
    header_row = target_table.find('tr')
    if header_row:
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    
    # Extract rows
    rows = []
    current_category = None
    
    for row in target_table.find_all('tr')[1:]:  # Skip header row
        cells = row.find_all(['th', 'td'])
        if not cells:
            continue
            
        row_data = [cell.get_text(strip=True) for cell in cells]
        
        # Skip empty rows
        if not any(row_data):
            continue
            
        # If the row starts with a non-numeric value and has fewer cells,
        # it might be a category header
        if len(row_data) < len(headers) and not row_data[0].replace('$', '').replace(',', '').replace('.', '').strip().isdigit():
            current_category = row_data[0]
            continue
            
        # Regular data row
        if len(row_data) == len(headers):
            line_item = row_data[0]
            amounts = row_data[1:]
            
            # Create a row for each fiscal quarter
            for i, amount in enumerate(amounts):
                fiscal_quarter = headers[i + 1]  # Skip the first header (line item name)
                rows.append({
                    'fiscal_quarter': fiscal_quarter,
                    'category': current_category,
                    'line_item': line_item,
                    'amount': amount,
                    'is_total': 'total' in line_item.lower() or 'total' in str(current_category).lower()
                })
    
    return pd.DataFrame(rows)


def validate_fiscal_quarter(quarter: str) -> bool:
    """
    Validate that the fiscal quarter string contains a valid date format.
    """
    cleaned = quarter.lower().strip()
    return any(month in cleaned for month in ['january', 'april', 'july', 'october']) and any(str(year) in cleaned for year in range(2020, 2025))


def validate_amount(amount: float) -> bool:
    """
    Validate that the amount is within reasonable bounds for a financial statement (in millions).
    """
    return -1_000_000 <= amount <= 1_000_000  # Reasonable range for amounts in millions


def validate_category(category: str) -> str:
    """
    Clean and validate category names, ensuring consistent formatting.
    """
    if not category or category == 'Uncategorized':
        return 'Uncategorized'
    
    # Remove common noise and standardize formatting
    cleaned = category.strip()
    cleaned = cleaned.replace(':', '').replace('(', '').replace(')', '')
    
    # Capitalize first letter of each word
    return ' '.join(word.capitalize() for word in cleaned.split())


def validate_line_item(item: str) -> str:
    """
    Clean and validate line item names, ensuring consistent formatting.
    """
    if not item:
        return 'Unknown'
    
    # Remove common noise and standardize formatting
    cleaned = item.strip()
    cleaned = cleaned.replace(':', '').replace('  ', ' ')
    
    # Special handling for parenthetical notes
    if '(' in cleaned and ')' in cleaned:
        main_text = cleaned.split('(')[0].strip()
        note = cleaned[cleaned.find('('):].strip()
        cleaned = f"{main_text} {note}"
    
    return cleaned


def detect_total_row(row: pd.Series) -> bool:
    """
    Enhanced detection of total rows using multiple indicators.
    """
    total_keywords = ['total', 'subtotal', 'net']
    line_item = str(row['line_item']).lower()
    category = str(row['category']).lower()
    
    # Check for explicit total indicators
    if any(keyword in line_item for keyword in total_keywords) or \
       any(keyword in category for keyword in total_keywords):
        return True
    
    # Check for common total row patterns
    if line_item.startswith('total') or category.startswith('total'):
        return True
    
    # Check for mathematical relationship with other rows
    # This would require context from other rows, which we'll handle in transform_data
    
    return False


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform and validate the extracted data into the required format with proper columns.
    """
    # Create a copy to avoid modifying the original DataFrame
    df = df.copy()
    
    # Clean and validate fiscal quarters
    df['fiscal_quarter'] = df['fiscal_quarter'].apply(lambda x: x.strip())
    invalid_quarters = df[~df['fiscal_quarter'].apply(validate_fiscal_quarter)]
    if not invalid_quarters.empty:
        print("Warning: Found invalid fiscal quarters:", invalid_quarters['fiscal_quarter'].unique(), file=sys.stderr)
    
    # Clean amount values and convert to numeric
    df['amount'] = df['amount'].apply(lambda x: x.replace('$', '').replace(',', '').strip())
    df['amount'] = df['amount'].apply(lambda x: 
        float(x.replace('(', '-').replace(')', '')) if x else 0
    )
    
    # Validate amounts
    invalid_amounts = df[~df['amount'].apply(validate_amount)]
    if not invalid_amounts.empty:
        print("Warning: Found unusually large or small amounts:", invalid_amounts[['line_item', 'amount']], file=sys.stderr)
    
    # Clean and validate categories and line items
    df['category'] = df['category'].apply(validate_category)
    df['line_item'] = df['line_item'].apply(validate_line_item)
    
    # Enhanced total row detection
    df['is_total'] = df.apply(detect_total_row, axis=1)
    
    # Validate total rows by checking mathematical relationships
    categories = df['category'].unique()
    for category in categories:
        category_data = df[df['category'] == category].copy()
        if category_data['is_total'].any():
            total_rows = category_data[category_data['is_total']]
            for _, total_row in total_rows.iterrows():
                non_total_sum = category_data[
                    (~category_data['is_total']) & 
                    (category_data['fiscal_quarter'] == total_row['fiscal_quarter'])
                ]['amount'].sum()
                if abs(total_row['amount'] - non_total_sum) > 0.01:  # Allow small rounding differences
                    print(f"Warning: Total mismatch in category '{category}' for {total_row['fiscal_quarter']}", file=sys.stderr)
    
    # Ensure proper column order
    column_order = ['fiscal_quarter', 'category', 'line_item', 'amount', 'is_total']
    df = df[column_order]
    
    return df


def validate_output_path(output_path: str) -> None:
    """
    Validate the output path for CSV export.
    """
    import os
    
    # Check if directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        raise ValueError(f"Output directory does not exist: {output_dir}")
    
    # Check if path ends with .csv
    if not output_path.lower().endswith('.csv'):
        raise ValueError("Output path must end with .csv extension")
    
    # Check if file already exists
    if os.path.exists(output_path):
        raise ValueError(f"Output file already exists: {output_path}")


def export_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Export the transformed DataFrame to a CSV file with validation.
    """
    try:
        # Validate the DataFrame
        if df.empty:
            raise ValueError("No data to export")
        
        required_columns = ['fiscal_quarter', 'category', 'line_item', 'amount', 'is_total']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Validate output path
        validate_output_path(output_path)
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        
        # Verify the export
        exported_df = pd.read_csv(output_path)
        if len(exported_df) != len(df):
            raise ValueError("Exported CSV row count does not match original data")
            
        print(f"Successfully exported {len(df)} rows to {output_path}")
        print(f"Data summary:")
        print(f"- Fiscal quarters: {', '.join(sorted(df['fiscal_quarter'].unique()))}")
        print(f"- Categories: {len(df['category'].unique())}")
        print(f"- Total rows: {df['is_total'].sum()}")
        
    except Exception as e:
        print(f"Error exporting to CSV: {e}", file=sys.stderr)
        sys.exit(1)


def validate_url(url: str) -> None:
    """
    Validate the input URL format.
    """
    import re
    
    sec_url_pattern = r'https?://www\.sec\.gov/Archives/edgar/data/.*\.htm'
    if not re.match(sec_url_pattern, url):
        raise ValueError("Invalid SEC URL format. URL must be from sec.gov/Archives/edgar/")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape SEC 10Q Balance Sheet data and export to CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  %(prog)s https://www.sec.gov/Archives/edgar/data/1045810/000104581024000124/nvda-20240428.htm output.csv

Notes:
  - The input URL must be a valid SEC EDGAR filing URL
  - The output path must end with .csv extension
  - The output directory must exist
  - The output file must not already exist
"""
    )
    parser.add_argument(
        'input_url',
        help='URL of the SEC 10Q filing (must be from sec.gov/Archives/edgar/)'
    )
    parser.add_argument(
        'output_path',
        help='Path for the output CSV file (must end with .csv)'
    )
    
    try:
        args = parser.parse_args()
        
        # Validate input URL
        validate_url(args.input_url)
        
        # Main execution flow with progress messages
        print("Fetching and parsing HTML content...")
        soup = fetch_and_parse_html(args.input_url)
        
        print("Extracting balance sheet data...")
        raw_data = extract_balance_sheet(soup)
        
        print("Transforming and validating data...")
        transformed_data = transform_data(raw_data)
        
        print("Exporting to CSV...")
        export_to_csv(transformed_data, args.output_path)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()