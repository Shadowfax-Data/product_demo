#!/usr/bin/env python3

import argparse
import os
import re
import requests
import pdfplumber
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import urlparse

def download_pdf(url: str, output_dir: str = "temp") -> str:
    """
    Download PDF from URL and save to a temporary directory.
    
    Args:
        url: URL of the PDF file
        output_dir: Directory to save the downloaded PDF
        
    Returns:
        Path to the downloaded PDF file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract filename from URL
    filename = os.path.basename(urlparse(url).path)
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    
    output_path = os.path.join(output_dir, filename)
    
    # Download the file
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return output_path

def find_balance_sheet_pages(pdf) -> List[int]:
    """
    Find all pages containing the consolidated balance sheets.
    
    Args:
        pdf: PDFPlumber PDF object
        
    Returns:
        List of page numbers containing balance sheet content
    """
    target_text = "Condensed Consolidated Balance Sheets"
    balance_sheet_pages = []
    balance_sheet_page_ref = None
    
    # First pass: find the page reference in the table of contents
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        print(f"Checking page {page_num}...")
        
        if "table of contents" in text.lower():
            print("Found table of contents, looking for balance sheet reference...")
            lines = text.split('\n')
            for line in lines:
                if target_text.lower() in line.lower():
                    # Try to extract the page number
                    parts = line.split()
                    try:
                        # The page number is usually the last number in the line
                        page_numbers = [int(p) for p in parts if p.isdigit()]
                        if page_numbers:
                            balance_sheet_page_ref = page_numbers[-1]
                            print(f"Found balance sheet reference to page {balance_sheet_page_ref}")
                            break
                    except ValueError:
                        continue
        
        if balance_sheet_page_ref is not None:
            break
    
    # Second pass: check all pages for balance sheet content
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text().lower()
        
        # Skip table of contents pages
        if "table of contents" in text:
            continue
            
        # Skip if this is not a balance sheet page
        if "statements of cash flows" in text:
            continue
            
        # Look for balance sheet content
        if any(term in text for term in [
            'assets', 'liabilities', 'cash and cash equivalents',
            'total current assets', 'stockholders'
        ]):
            # Verify this is actually a balance sheet page by checking for multiple indicators
            indicators = [
                'cash and cash equivalents',
                'accounts receivable',
                'total assets',
                'accounts payable',
                'current assets',
                'current liabilities',
                'stockholders'
            ]
            
            indicator_count = sum(1 for term in indicators if term in text)
            if indicator_count >= 2:  # Require at least 2 indicators
                print(f"Found balance sheet content on page {page_num}")
                print("Page content:")
                print(text[:500])
                balance_sheet_pages.append(page_num)
                
                # Also check the next page, as balance sheets often span multiple pages
                if page_num + 1 < len(pdf.pages):
                    next_text = pdf.pages[page_num + 1].extract_text().lower()
                    if "statements of cash flows" not in next_text:
                        next_indicator_count = sum(1 for term in indicators if term in next_text)
                        if next_indicator_count >= 1:  # Require at least 1 indicator for continuation
                            print(f"Found balance sheet continuation on page {page_num + 1}")
                            balance_sheet_pages.append(page_num + 1)
    
    if not balance_sheet_pages and balance_sheet_page_ref is not None:
        # If we found a reference but no content, check around the referenced page
        start_page = max(0, balance_sheet_page_ref - 2)
        end_page = min(len(pdf.pages), balance_sheet_page_ref + 3)
        
        for page_num in range(start_page, end_page):
            text = pdf.pages[page_num].extract_text().lower()
            if "statements of cash flows" not in text and any(term in text for term in [
                'cash and cash equivalents',
                'accounts receivable',
                'total assets',
                'accounts payable'
            ]):
                print(f"Found balance sheet content on referenced page {page_num}")
                balance_sheet_pages.append(page_num)
    
    return sorted(list(set(balance_sheet_pages)))

def extract_balance_sheet(pdf_path: str) -> pd.DataFrame:
    """
    Extract balance sheet data from the PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        DataFrame containing the balance sheet data
    """
    with pdfplumber.open(pdf_path) as pdf:
        # Find all pages containing balance sheet data
        pages = find_balance_sheet_pages(pdf)
        if not pages:
            raise ValueError("Could not find balance sheet table in the PDF")
            
        # Extract data from all pages
        all_data = []
        headers = None
        
        for page_num in pages:
            table_data = extract_balance_sheet_table(pdf, page_num)
            if not headers:
                headers = table_data[0]
                all_data.extend(table_data[1:])
            else:
                # Skip the header row for subsequent pages
                all_data.extend(table_data[1:])
        
        # Combine all data with headers
        table_data = [headers] + all_data
        
        # Process the combined data
        df = process_table_data(table_data)
        
        return df

def clean_number(value_str: str) -> Optional[float]:
    """Clean and convert a string to a number."""
    try:
        # Remove currency symbols and commas
        cleaned = value_str.replace('$', '').replace(',', '').strip()
        if cleaned:
            return float(cleaned)
    except (ValueError, TypeError):
        pass
    return None

def clean_label(text: str) -> str:
    """Clean a label by removing numbers and special characters."""
    # Remove any numbers and their surrounding text
    text = re.sub(r'\s*\d+(?:,\d+)*(?:\.\d+)?\s*(?:and|shares?)?\s*', ' ', text)
    # Remove special characters
    text = re.sub(r'[;,]$', '', text)
    # Remove any text after $ symbol
    text = text.split('$')[0]
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_section_header(text: str) -> bool:
    """Check if a line is a section header."""
    text_lower = text.lower()
    section_keywords = ['assets', 'liabilities', "stockholders'", 'equity']
    
    # Skip if this is a data line
    if any(c.isdigit() for c in text) or '$' in text:
        return False
        
    # Check for section keywords
    if any(keyword in text_lower for keyword in section_keywords):
        words = text_lower.split()
        # Check if this is actually a section header
        if any(word in section_keywords for word in words):
            if 'total' not in text_lower:
                return True
    
    return False

def extract_balance_sheet_table(pdf, page_num: int) -> List[List[str]]:
    """
    Extract the balance sheet table from the specified page.
    
    Args:
        pdf: PDFPlumber PDF object
        page_num: Page number containing the balance sheet
        
    Returns:
        List of rows containing table data
    """
    page = pdf.pages[page_num]
    
    print(f"\nExtracting text with layout information from page {page_num}...")
    
    # Extract all text elements with their positions
    words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=True)
    
    # Group words by their y-position (lines)
    y_positions = {}
    for word in words:
        y = round(word['top'])  # Round to handle small variations
        if y not in y_positions:
            y_positions[y] = []
        y_positions[y].append(word)
    
    # Sort lines by y-position
    sorted_lines = []
    for y in sorted(y_positions.keys()):
        # Sort words in line by x-position
        line_words = sorted(y_positions[y], key=lambda w: w['x0'])
        sorted_lines.append(line_words)
    
    # Process lines to create table-like structure
    table_lines = []
    current_section = None
    current_subsection = None
    date_line = None
    
    # Patterns for matching
    number_pattern = r'\$?\s*([\d,]+(?:\.\d+)?)'
    section_keywords = ['assets', 'liabilities', "stockholders'", 'equity']
    
    print("Processing lines...")
    for line_words in sorted_lines:
        # Combine words into a line
        line = ' '.join(word['text'] for word in line_words)
        line = line.strip()
        if not line:
            continue
        
        line_lower = line.lower()
        print(f"Line: {line}")
        
        # Skip header lines
        if any(skip in line_lower for skip in ['snowflake inc.', 'condensed consolidated', '(in thousands', '(unaudited)']):
            print("Skipping header line")
            continue
            
        # Skip if this is not a balance sheet page
        if 'statements of cash flows' in line_lower:
            print("Not a balance sheet page")
            break
            
        # Capture the date line
        if 'as of' in line_lower or ('april' in line_lower and 'january' in line_lower):
            print("Found date line")
            date_line = line
            continue
            
        # Identify main sections
        if is_section_header(line):
            print(f"Found section: {line}")
            current_section = clean_label(line)
            current_subsection = None
            continue
            
        # Identify subsections
        if ':' in line and not any(c.isdigit() for c in line):
            print(f"Found subsection: {line}")
            current_subsection = clean_label(line.rstrip(':'))
            continue
            
        # Process data lines
        if any(c.isdigit() for c in line):
            # Try to extract label and values
            # First, try to split by $
            parts = line.split('$')
            if len(parts) > 1:
                label = parts[0].strip()
                values = ['$' + p.strip() for p in parts[1:]]
            else:
                # If no $, try to split by spaces and look for numbers
                words = line.split()
                label_parts = []
                value_parts = []
                for word in words:
                    if any(c.isdigit() for c in word) or word in ['-', '—']:
                        value_parts.append(word)
                    else:
                        label_parts.append(word)
                label = ' '.join(label_parts).strip()
                values = [' '.join(value_parts)]
            
            if label:
                # Extract numbers from values
                numbers = []
                for value in values:
                    matches = re.findall(number_pattern, value)
                    numbers.extend(matches)
                
                if numbers:
                    # Clean up the label
                    label = clean_label(label)
                    
                    # Build the full label with section hierarchy
                    full_label = label
                    if current_subsection and 'total' not in label.lower():
                        full_label = f"{current_subsection} - {label}"
                    if current_section and 'total' not in label.lower():
                        full_label = f"{current_section} - {full_label}"
                    
                    # Clean up the values
                    cleaned_values = []
                    for value in numbers:
                        cleaned_value = clean_number(value)
                        if cleaned_value is not None:
                            cleaned_values.append(str(cleaned_value))
                    
                    if cleaned_values and len(cleaned_values) <= 2:  # Only accept rows with 1 or 2 values
                        # Skip if this is not a balance sheet item
                        if not any(term in full_label.lower() for term in [
                            'assets', 'liabilities', 'equity', 'cash', 'investments',
                            'receivable', 'payable', 'revenue', 'stock'
                        ]):
                            continue
                            
                        print(f"Found data row: {full_label} -> {cleaned_values}")
                        table_lines.append([full_label] + cleaned_values)
    
    if not table_lines:
        print("No table lines found!")
        raise ValueError("Could not extract balance sheet data")
    
    # Process the date line to create headers
    headers = ['Item']
    if date_line:
        # Extract dates from the date line
        dates = re.findall(r'(?:January|April)\s+\d+,\s+\d{4}', date_line)
        if dates:
            headers.extend(dates)
        else:
            # Try to find dates in the format MM/DD/YYYY
            dates = re.findall(r'\d{2}/\d{2}/\d{4}', date_line)
            if dates:
                headers.extend(dates)
            else:
                headers.extend(['Date 1', 'Date 2'])
    else:
        headers.extend(['Date 1', 'Date 2'])
    
    print(f"Found {len(table_lines)} data rows")
    print("Headers:", headers)
    
    # Combine headers with data
    table_data = [headers] + table_lines
    
    return table_data

def validate_date_columns(df: pd.DataFrame) -> bool:
    """
    Validate that the column headers contain valid dates.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if dates are valid, False otherwise
    """
    date_cols = df.columns[1:]  # Skip 'Item' column
    date_patterns = [
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
        r'\d{2}/\d{2}/\d{4}'
    ]
    
    for col in date_cols:
        if not any(re.match(pattern, str(col)) for pattern in date_patterns):
            print(f"Warning: Invalid date format in column header: {col}")
            return False
    return True

def validate_numeric_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean numeric values in the DataFrame.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Cleaned DataFrame
    """
    numeric_cols = df.columns[1:]  # Skip 'Item' column
    
    for col in numeric_cols:
        # Convert to numeric, coerce errors to NaN
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Check for outliers using IQR method
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Flag outliers
        outliers = df[col][(df[col] < lower_bound) | (df[col] > upper_bound)]
        if not outliers.empty:
            print(f"\nWarning: Found {len(outliers)} outliers in column {col}:")
            for idx in outliers.index:
                print(f"  * {df.loc[idx, 'Item']}: {outliers[idx]:,.2f}")
    
    return df

def validate_balance_sheet_equation(df: pd.DataFrame, tolerance: float = 0.01) -> bool:
    """
    Validate that total assets = total liabilities + total equity.
    
    Args:
        df: DataFrame to validate
        tolerance: Acceptable difference ratio
        
    Returns:
        True if equation holds within tolerance, False otherwise
    """
    # Find total assets, liabilities, and equity
    total_assets = None
    total_liabilities = None
    total_equity = None
    
    for idx, row in df.iterrows():
        label = row['Item'].lower()
        if 'total assets' in label:
            total_assets = df.iloc[idx, 1:].values
        elif 'total liabilities' in label:
            total_liabilities = df.iloc[idx, 1:].values
        elif "total stockholders'" in label and 'equity' in label:
            total_equity = df.iloc[idx, 1:].values
    
    if total_assets is None or total_liabilities is None or total_equity is None:
        print("Warning: Could not find all required totals")
        return False
    
    # Check equation for each date column
    for i in range(len(total_assets)):
        if pd.isna(total_assets[i]) or pd.isna(total_liabilities[i]) or pd.isna(total_equity[i]):
            continue
            
        diff = abs(total_assets[i] - (total_liabilities[i] + total_equity[i]))
        if diff > total_assets[i] * tolerance:
            print(f"\nWarning: Balance sheet equation doesn't hold for {df.columns[i+1]}:")
            print(f"  * Total Assets: {total_assets[i]:,.2f}")
            print(f"  * Total Liabilities + Equity: {(total_liabilities[i] + total_equity[i]):,.2f}")
            print(f"  * Difference: {diff:,.2f}")
            return False
    
    return True

def validate_required_items(df: pd.DataFrame) -> bool:
    """
    Validate that all required balance sheet items are present.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if all required items are present, False otherwise
    """
    required_items = [
        'cash', 'total assets', 'total liabilities', 'equity',
        'accounts receivable', 'accounts payable'
    ]
    
    missing_items = []
    for item in required_items:
        if not any(item in row['Item'].lower() for _, row in df.iterrows()):
            missing_items.append(item)
    
    if missing_items:
        print("\nWarning: Missing required balance sheet items:")
        for item in missing_items:
            print(f"  * {item}")
        return False
    
    return True

def process_table_data(table_data: List[List[str]]) -> pd.DataFrame:
    """
    Process and structure the extracted table data into a DataFrame.

    Args:
        table_data: Raw table data as list of lists

    Returns:
        Processed DataFrame
    """
    print("\nProcessing table data...")
    # Convert to DataFrame
    df = pd.DataFrame(table_data[1:], columns=table_data[0])
    print(f"Initial shape: {df.shape}")
    print("Headers:", df.columns.tolist())

    # Clean up the data
    for col in df.columns[1:]:  # Skip the 'Item' column
        df[col] = df[col].apply(lambda x: x.replace('$', '').replace(',', '').strip() if pd.notnull(x) else "")
        df[col] = df[col].replace('', np.nan)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Validate the data
    print("\nValidating data...")

    # Check date columns
    if not validate_date_columns(df):
        print("Warning: Invalid date columns found")

    # Validate numeric values and check for outliers
    df = validate_numeric_values(df)

    # Check for required items
    if not validate_required_items(df):
        print("Warning: Some required balance sheet items are missing")

    # Validate balance sheet equation
    if not validate_balance_sheet_equation(df):
        print("Warning: Balance sheet equation validation failed")

    # Remove rows where all numeric columns are NaN
    df = df.dropna(subset=df.columns[1:], how='all')

    print(f"\nFinal shape after cleaning: {df.shape}")
    return df

def export_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Export the DataFrame to a CSV file with enhanced output and validation.
    
    Args:
        df: DataFrame to export
        output_path: Path where the CSV file should be saved
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        
        # Print summary statistics
        print(f"\nData exported successfully to: {output_path}")
        print(f"Number of rows: {len(df)}")
        print(f"Columns: {', '.join(df.columns)}")
        
        # Display data quality metrics
        numeric_cols = df.columns[1:]  # Skip 'Item' column
        print("\nData Quality Summary:")
        print(f"- Missing values: {df[numeric_cols].isnull().sum().sum()} total")
        print("- Column-wise missing values:")
        for col in numeric_cols:
            missing = df[col].isnull().sum()
            if missing > 0:
                print(f"  * {col}: {missing} missing values")
        
        # Display sample of the data
        print("\nFirst few rows of the exported data:")
        print(df.head().to_string())
        
        # Display value ranges for numeric columns
        print("\nValue ranges for numeric columns:")
        for col in numeric_cols:
            if df[col].notna().any():
                print(f"- {col}:")
                print(f"  * Min: {df[col].min():,.2f}")
                print(f"  * Max: {df[col].max():,.2f}")
                print(f"  * Mean: {df[col].mean():,.2f}")
        
    except Exception as e:
        raise IOError(f"Error saving CSV file: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description='Extract financial data from Snowflake quarterly reports'
    )
    parser.add_argument(
        'url',
        help='URL of the Snowflake financial statement PDF'
    )
    parser.add_argument(
        'output',
        help='Path to save the output CSV file'
    )
    parser.add_argument(
        '--temp-dir',
        default='temp',
        help='Directory to store temporary files (default: temp)'
    )

    args = parser.parse_args()

    try:
        # Download the PDF file
        pdf_path = download_pdf(args.url, args.temp_dir)
        print(f"Successfully downloaded PDF to: {pdf_path}")

        # Extract balance sheet data
        df = extract_balance_sheet(pdf_path)
        print("Successfully extracted balance sheet data")

        # Export to CSV with enhanced output
        export_to_csv(df, args.output)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return 1
    except ValueError as e:
        print(f"Error extracting data: {e}")
        return 1
    except IOError as e:
        print(str(e))
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())