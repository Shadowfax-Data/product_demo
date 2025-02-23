#!/usr/bin/env python3

import os
import sys
import requests
import camelot
import PyPDF2
import argparse
from typing import Tuple, List
import re
import pandas as pd
import numpy as np
from datetime import datetime

def extract_fiscal_quarter(url: str) -> str:
    """
    Extract fiscal quarter information from the PDF URL or filename.
    Returns a string like 'FY25Q1'.
    """
    # Extract Q1/Q2/Q3/Q4 and FY year from the URL
    quarter_match = re.search(r'[Qq](\d)', url)
    fy_match = re.search(r'FY(\d{2})', url)
    
    if not quarter_match or not fy_match:
        raise ValueError("Could not extract fiscal quarter information from URL")
    
    quarter = quarter_match.group(1)
    fy = fy_match.group(1)
    return f"FY{fy}Q{quarter}"

def clean_amount(amount: str) -> Tuple[float, bool]:
    """
    Clean amount string and determine if it's valid.
    Returns tuple of (float amount, is_valid).
    """
    if not amount or amount.strip() == '':
        return 0.0, False
        
    # Remove $ and , characters
    amount = amount.replace('$', '').replace(',', '')
    
    # Handle multiple numbers in the string
    parts = amount.split()
    if len(parts) > 1:
        # Try each part until we find a valid number
        for part in parts:
            try:
                # Handle parentheses for negative numbers
                if '(' in part and ')' in part:
                    part = part.replace('(', '').replace(')', '')
                    return -float(part), True
                return float(part), True
            except ValueError:
                continue
        return 0.0, False
    
    try:
        # Handle parentheses for negative numbers
        if '(' in amount and ')' in amount:
            amount = amount.replace('(', '').replace(')', '')
            return -float(amount), True
        return float(amount), True
    except ValueError:
        return 0.0, False

def is_total_row(row: List[str], prev_rows: List[List[str]] = None) -> bool:
    """
    Determine if a row represents a total/subtotal based on keywords, formatting,
    and context from previous rows.
    """
    if not row:
        return False
    
    first_cell = row[0].lower().strip()
    
    # Direct total indicators
    total_keywords = ['total', 'net', 'gross']
    if any(keyword in first_cell for keyword in total_keywords):
        return True
    
    # Check for indentation patterns if we have previous rows
    if prev_rows and len(prev_rows) >= 2:
        # If this row starts with "Total" and previous rows were indented
        if first_cell.startswith('total '):
            return True
        
        # If this row has a number and previous rows were subcategories
        prev_categories = set(r[0].strip() for r in prev_rows[-2:])
        if len(prev_categories) > 1 and any(c.startswith('    ') for c in prev_categories):
            return True
    
    # Check for common total line items
    total_items = [
        'total assets',
        'total current assets',
        'total liabilities',
        'total current liabilities',
        "total stockholders' equity",
        "total liabilities and stockholders' equity"
    ]
    return any(item in first_cell for item in total_items)

def determine_category(row: List[str], prev_category: str) -> str:
    """
    Determine the category for a row based on its content and formatting.
    """
    if not row or not row[0].strip():
        return prev_category
        
    first_cell = row[0].strip().lower()
    
    # Check for main categories
    if first_cell == 'assets' or first_cell == 'current assets:':
        return 'Assets'
    elif first_cell == 'liabilities' or first_cell == 'current liabilities:':
        return 'Liabilities'
    elif any(equity in first_cell for equity in ["stockholders' equity", "shareholders' equity"]):
        return "Stockholders' Equity"
    elif first_cell.endswith(':') and not first_cell.startswith('    '):
        # Handle subcategories
        if 'assets' in first_cell:
            return 'Assets'
        elif 'liabilities' in first_cell:
            return 'Liabilities'
        elif 'equity' in first_cell:
            return "Stockholders' Equity"
    
    # Check for category changes based on line items
    if 'accounts payable' in first_cell or 'deferred revenue' in first_cell:
        return 'Liabilities'
    elif 'common stock' in first_cell or 'accumulated deficit' in first_cell:
        return "Stockholders' Equity"
    
    # Keep the current category for line items
    return prev_category

def find_balance_sheet_table(tables: List[List[List[str]]]) -> List[List[str]]:
    """
    Find the table containing the balance sheet data.
    Returns the table containing the balance sheet.
    """
    best_table = None
    max_score = 0
    
    balance_sheet_keywords = [
        'assets', 'liabilities', 'cash', 'receivables', 'inventory',
        'current assets', 'total assets', 'accounts payable',
        "stockholders' equity", "shareholders' equity"
    ]
    
    for table in tables:
        score = 0
        found_keywords = set()
        
        # Join all text in the table
        table_text = ' '.join(' '.join(cell.lower() for cell in row) for row in table)
        
        # Count unique keywords found
        for keyword in balance_sheet_keywords:
            if keyword in table_text:
                found_keywords.add(keyword)
                score += 1
        
        # Bonus points for having both assets and liabilities
        if 'assets' in found_keywords and 'liabilities' in found_keywords:
            score += 3
            
        # Bonus points for having equity section
        if any(equity in found_keywords for equity in ["stockholders' equity", "shareholders' equity"]):
            score += 2
            
        # Check if this table has the highest score
        if score > max_score:
            max_score = score
            best_table = table
    
    if best_table is None or max_score < 3:  # Require at least 3 keywords
        raise ValueError("Could not find balance sheet table")
        
    return best_table

def clean_and_structure_data(tables: List[List[List[str]]], fiscal_quarter: str) -> List[dict]:
    """
    Clean and structure the extracted table data into the required format.
    Returns a list of dictionaries with the required fields.
    """
    structured_data = []
    current_category = 'Assets'  # Default starting category
    previous_rows = []
    
    # Find the balance sheet table
    if not tables:
        raise ValueError("No tables found")
    
    table = find_balance_sheet_table(tables)
    
    # Process each row
    for row in table:
        # Skip empty rows or rows without content
        if not any(cell.strip() for cell in row):
            continue
            
        line_item = row[0].strip()
        if not line_item:
            continue
            
        # Skip header rows and non-financial rows
        if any(skip in line_item.lower() for skip in 
            ['consolidated', 'unaudited', 'in thousands', 'see accompanying', 'as of']):
            continue
            
        # Update category if needed
        new_category = determine_category(row, current_category)
        if new_category != current_category:
            current_category = new_category
            if current_category in ['Assets', 'Liabilities', "Stockholders' Equity"]:
                continue
            
        # Usually the most recent quarter's data is in the second column
        # Some tables might have the amount in the third column
        amount_str = ''
        for col in row[1:]:
            cleaned = col.strip()
            if cleaned and any(c.isdigit() for c in cleaned):
                amount_str = cleaned
                break
                
        amount, is_valid = clean_amount(amount_str)
        
        if not is_valid:
            continue
            
        # Determine if this is a total row using context from previous rows
        is_total_value = is_total_row(row, previous_rows)
        
        # Clean up line item name
        line_item = re.sub(r'\s+', ' ', line_item).strip()
        
        # Skip rows that don't look like financial data
        if len(line_item.split()) <= 1 and not any(c.isdigit() for c in line_item):
            continue
            
        # Skip rows that are just dates or headers
        if any(skip in line_item.lower() for skip in [
            'authorized', 'issued', 'par value', 'shares', 'class', 'stock', 'each'
        ]):
            continue
            
        # Add the row to structured data
        structured_data.append({
            'fiscal_quarter': fiscal_quarter,
            'category': current_category,
            'line_item': line_item,
            'amount': amount,
            'is_total': is_total_value
        })
        
        # Update previous rows for context
        previous_rows.append(row)
        if len(previous_rows) > 3:  # Keep only last 3 rows for context
            previous_rows.pop(0)
    
    return structured_data

def download_pdf(url: str, output_path: str) -> str:
    """
    Download a PDF from a URL and save it to the specified path.
    Returns the path to the downloaded file.
    """
    response = requests.get(url)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    return output_path

def find_balance_sheet_page(pdf_path: str) -> int:
    """
    Find the page number containing the consolidated balance sheet.
    Returns the page number (1-based index).
    """
    print("\nSearching for balance sheet page...")
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"PDF has {len(pdf_reader.pages)} pages")
        
        # First pass: look for the balance sheet in the table of contents
        balance_sheet_page = None
        for page_num in range(len(pdf_reader.pages)):
            text = pdf_reader.pages[page_num].extract_text().lower()
            print(f"\nChecking page {page_num + 1}...")
            print(f"First 200 characters: {text[:200]}...")
            
            if 'table of contents' in text and 'condensed consolidated balance sheets' in text:
                # Try to find the page number reference
                lines = text.split('\n')
                for line in lines:
                    if 'condensed consolidated balance sheets' in line.lower():
                        # Try to extract the page number
                        parts = line.split()
                        try:
                            page_ref = int(parts[-1])
                            balance_sheet_page = page_ref
                            print(f"Found balance sheet reference to page {page_ref}")
                            break
                        except (ValueError, IndexError):
                            continue
            
            if balance_sheet_page is not None:
                break
        
        # Second pass: verify the actual balance sheet page
        if balance_sheet_page is not None:
            text = pdf_reader.pages[balance_sheet_page - 1].extract_text().lower()
            if 'condensed consolidated balance sheets' in text and \
               ('(in thousands' in text or '$' in text):
                print(f"Verified balance sheet on page {balance_sheet_page}")
                return balance_sheet_page
        
        # Third pass: look for the balance sheet directly
        for page_num in range(len(pdf_reader.pages)):
            text = pdf_reader.pages[page_num].extract_text().lower()
            
            # Skip obvious non-balance sheet pages
            if 'table of contents' in text and 'financial statements' not in text:
                continue
                
            # Look for the balance sheet with financial data
            if 'condensed consolidated balance sheets' in text:
                # Verify it's the actual balance sheet
                if ('(in thousands' in text or '$' in text) and \
                   ('assets' in text or 'liabilities' in text):
                    print(f"Found balance sheet with financial data on page {page_num + 1}")
                    return page_num + 1
        
        # Fourth pass: look for any page that looks like a balance sheet
        for page_num in range(len(pdf_reader.pages)):
            text = pdf_reader.pages[page_num].extract_text().lower()
            
            # Skip obvious non-balance sheet pages
            if any(skip in text for skip in ['table of contents', 'notes to', 'exhibit']):
                continue
                
            # Look for combinations of financial terms that indicate a balance sheet
            financial_terms = {
                'assets': ['current assets', 'total assets', 'cash and', 'receivable'],
                'liabilities': ['current liabilities', 'total liabilities', 'accounts payable'],
                'equity': ["stockholders' equity", "shareholders' equity", 'common stock']
            }
            
            # Count terms from each category found in the text
            categories_found = 0
            for category_terms in financial_terms.values():
                if any(term in text for term in category_terms):
                    categories_found += 1
            
            # If we find terms from at least 2 categories and see financial data
            if categories_found >= 2 and ('$' in text or '(in thousands' in text):
                print(f"Found balance sheet by structure on page {page_num + 1}")
                return page_num + 1
    
    raise ValueError("Could not find balance sheet page in the PDF")

def extract_page_to_new_pdf(input_pdf: str, page_number: int, output_pdf: str) -> str:
    """
    Extract a specific page from the input PDF and save it as a new PDF.
    Returns the path to the new PDF file.
    """
    with open(input_pdf, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Page numbers are 0-based in PyPDF2
        page = pdf_reader.pages[page_number - 1]
        pdf_writer.add_page(page)
        
        with open(output_pdf, 'wb') as output_file:
            pdf_writer.write(output_file)
    
    return output_pdf

def extract_tables(pdf_path: str) -> List[List[List[str]]]:
    """
    Extract tables from the PDF using Camelot.
    Returns a list of tables, where each table is a list of rows.
    """
    # Try different table extraction methods
    tables = []
    
    print("Attempting table extraction with lattice flavor...")
    # Try lattice with different settings
    lattice_settings = [
        {'line_scale': 40},  # Default
        {'line_scale': 60},  # More aggressive line detection
        {'line_scale': 80}   # Most aggressive
    ]
    
    for settings in lattice_settings:
        try:
            tables_lattice = camelot.read_pdf(
                pdf_path, 
                pages='1', 
                flavor='lattice',
                **settings
            )
            if tables_lattice:
                print(f"Found {len(tables_lattice)} tables with lattice method (settings: {settings})")
                # Check if any table looks like a balance sheet
                for table in tables_lattice:
                    table_text = str(table.df).lower()
                    # Calculate score based on balance sheet terms
                    score = 0
                    if 'current assets' in table_text: score += 1
                    if 'total assets' in table_text: score += 1
                    if 'liabilities' in table_text: score += 1
                    if "stockholders' equity" in table_text: score += 2
                    if 'total liabilities' in table_text: score += 1
                    
                    if score >= 2:  # Accept if we find enough balance sheet terms
                        tables.append(table)
                        print(f"Found balance sheet table with lattice method (score: {score})")
        except Exception as e:
            print(f"Lattice extraction failed with settings {settings}: {str(e)}")
    
    # Try stream with different settings if needed
    print("Attempting table extraction with stream flavor...")
    stream_settings = [
        {
            'edge_tol': 50,
            'row_tol': 10,
            'strip_text': '\n',
            'flag_size': True
        },
        {
            'edge_tol': 100,
            'row_tol': 15,
            'strip_text': '\n',
            'split_text': True,
            'flag_size': True
        }
    ]
    
    for settings in stream_settings:
        try:
            # Try with different table areas to catch all sections
            table_areas = [
                None,  # Default full page
                ['0,700,600,100'],  # Top section
                ['0,400,600,0']  # Bottom section
            ]
            
            for area in table_areas:
                settings_copy = settings.copy()
                if area:
                    settings_copy['table_areas'] = area
                
                tables_stream = camelot.read_pdf(
                    pdf_path, 
                    pages='1', 
                    flavor='stream',
                    **settings_copy
                )
                if tables_stream:
                    print(f"Found {len(tables_stream)} tables with stream method (settings: {settings}, area: {area})")
                    # Check if any table looks like a balance sheet
                    for table in tables_stream:
                        table_text = str(table.df).lower()
                        # Calculate score based on balance sheet terms
                        score = 0
                        if 'current assets' in table_text: score += 1
                        if 'total assets' in table_text: score += 1
                        if 'liabilities' in table_text: score += 1
                        if "stockholders' equity" in table_text: score += 2
                        if 'total liabilities' in table_text: score += 1
                        
                        if score >= 2:  # Accept if we find enough balance sheet terms
                            tables.append(table)
                            print(f"Found balance sheet table with stream method (score: {score})")
        except Exception as e:
            print(f"Stream extraction failed with settings {settings}: {str(e)}")
    
    if not tables:
        raise ValueError("No tables found in the PDF")
    
    print("\nCleaning and processing extracted tables...")
    # Convert tables to list format and clean empty cells
    cleaned_tables = []
    for i, table in enumerate(tables):
        data = table.data
        print(f"\nTable {i+1} raw data (accuracy: {table.accuracy}):")
        print(f"Dimensions: {len(data)} rows x {len(data[0]) if data else 0} columns")
        for row in data[:5]:  # Print first 5 rows for debugging
            print(row)
        
        # Clean empty cells and normalize whitespace
        cleaned_data = []
        for row in data:
            # Skip rows that are completely empty or contain only whitespace
            if not any(cell.strip() for cell in row):
                continue
            
            # Clean and normalize each cell
            cleaned_row = []
            for cell in row:
                cell = cell.strip()
                # Normalize multiple spaces and newlines
                cell = re.sub(r'\s+', ' ', cell)
                # Remove any remaining special characters except those needed for numbers
                cell = re.sub(r'[^\w\s$(),.%-]', '', cell)
                cleaned_row.append(cell)
            
            # Only add rows that have actual content and look like balance sheet data
            if any(cell.strip() for cell in cleaned_row):
                line_item = cleaned_row[0].lower()
                
                # Skip header and non-financial rows
                if any(skip in line_item for skip in [
                    'see accompanying', 'notes', 'table of', 'authorized', 'issued',
                    'par value', 'shares', 'class', 'stock', 'each'
                ]):
                    continue
                    
                # Skip rows that don't have any numbers
                if not any(c.isdigit() for c in ''.join(cleaned_row[1:])):
                    continue
                    
                # Skip rows that are just dates or single words
                if len(line_item.split()) <= 1 and not any(c.isdigit() for c in line_item):
                    continue
                    
                cleaned_data.append(cleaned_row)
        
        if cleaned_data:
            cleaned_tables.append(cleaned_data)
            print(f"\nCleaned table {i+1} first 5 rows:")
            for row in cleaned_data[:5]:
                print(row)
    
    # Merge tables if we found multiple parts of the balance sheet
    if len(cleaned_tables) > 1:
        print("\nMerging multiple tables...")
        merged_table = []
        seen_rows = set()
        
        # Find the best table (usually the one with the most rows)
        best_table = max(cleaned_tables, key=len)
        
        # Track categories across tables
        current_category = None
        for row in best_table:
            # Skip empty rows
            if not any(c.strip() for c in row):
                continue
                
            # Update category if needed
            new_category = determine_category(row, current_category)
            if new_category != current_category:
                current_category = new_category
                # Add category header if it's a main category
                if current_category in ['Assets', 'Liabilities', "Stockholders' Equity"]:
                    category_row = [current_category, '', '', '', '']
                    row_key = '|'.join(category_row)
                    if row_key not in seen_rows:
                        merged_table.append(category_row)
                        seen_rows.add(row_key)
            
            # Add the row if it has financial data
            if any(c.isdigit() for c in ''.join(row[1:])):
                row_key = '|'.join(row)
                if row_key not in seen_rows:
                    merged_table.append(row)
                    seen_rows.add(row_key)
        
        # Add unique rows from other tables
        for table in cleaned_tables:
            if table is not best_table:
                for row in table:
                    # Skip rows that don't look like financial data
                    if not any(c.strip() for c in row):
                        continue
                    if not any(c.isdigit() for c in row[1:]):
                        continue
                        
                    # Clean up any merged cells
                    line_item = row[0].strip()
                    if len(line_item.split()) > 3:
                        # Try to split merged cells
                        parts = line_item.split()
                        for part in parts:
                            if len(part) > 3 and not any(skip in part.lower() for skip in ['total', 'and', 'other']):
                                # Create a new row for each part
                                new_row = row.copy()
                                new_row[0] = part
                                row_key = '|'.join(new_row)
                                if row_key not in seen_rows:
                                    merged_table.append(new_row)
                                    seen_rows.add(row_key)
                    else:
                        # Add the row as is
                        row_key = '|'.join(row)
                        if row_key not in seen_rows:
                            merged_table.append(row)
                            seen_rows.add(row_key)
        
        return [merged_table]
    
    return cleaned_tables

def process_pdf(url: str, temp_dir: str = '/tmp') -> Tuple[str, List[dict]]:
    """
    Process a PDF URL by downloading it, finding the balance sheet page,
    extracting it to a new PDF, and extracting the tables.
    Returns the path to the processed PDF and the structured data.
    """
    # Create a filename from the URL
    filename = url.split('/')[-1]
    base_name = os.path.splitext(filename)[0]
    
    # Extract fiscal quarter information
    fiscal_quarter = extract_fiscal_quarter(url)
    
    # Download the PDF
    pdf_path = os.path.join(temp_dir, filename)
    download_pdf(url, pdf_path)
    
    # Find the balance sheet page
    page_number = find_balance_sheet_page(pdf_path)
    
    # Extract the page to a new PDF
    extracted_pdf = os.path.join(temp_dir, f"{base_name}_balance_sheet.pdf")
    extract_page_to_new_pdf(pdf_path, page_number, extracted_pdf)
    
    # Extract tables from the new PDF
    tables = extract_tables(extracted_pdf)
    
    # Clean and structure the data
    structured_data = clean_and_structure_data(tables, fiscal_quarter)
    
    return extracted_pdf, structured_data

def save_to_csv(data: List[dict], output_path: str):
    """
    Save the structured data to a CSV file.
    """
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)

def validate_url(url: str) -> bool:
    """
    Validate that the URL points to a PDF file.
    """
    if not url.startswith('http'):
        return False
    if not url.lower().endswith('.pdf'):
        return False
    try:
        response = requests.head(url)
        return response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', '')
    except requests.RequestException:
        return False

def validate_output_path(path: str) -> bool:
    """
    Validate that the output path is writable and has a .csv extension.
    """
    if not path.lower().endswith('.csv'):
        return False
    try:
        dir_path = os.path.dirname(path) or '.'
        return os.access(dir_path, os.W_OK)
    except OSError:
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Extract balance sheet data from Snowflake financial statements.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -u https://example.com/financial.pdf -o output.csv
  %(prog)s --url https://example.com/financial.pdf --output /path/to/output.csv
        """
    )
    
    parser.add_argument(
        '-u', '--url',
        required=True,
        help='URL of the Snowflake financial statement PDF'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Path to save the output CSV file'
    )
    
    parser.add_argument(
        '-t', '--temp-dir',
        default='/tmp',
        help='Directory for temporary files (default: /tmp)'
    )
    
    args = parser.parse_args()
    
    # Validate URL
    if not validate_url(args.url):
        parser.error(f"Invalid or inaccessible PDF URL: {args.url}")
    
    # Validate output path
    if not validate_output_path(args.output):
        parser.error(f"Invalid or non-writable output path: {args.output}")
    
    # Validate temp directory
    if not os.path.isdir(args.temp_dir) or not os.access(args.temp_dir, os.W_OK):
        parser.error(f"Invalid or non-writable temporary directory: {args.temp_dir}")
    
    try:
        # Process the PDF and extract data
        fiscal_quarter, data = process_pdf(args.url, args.temp_dir)
        
        if not data:
            print("Error: No balance sheet data was extracted from the PDF", file=sys.stderr)
            sys.exit(1)
        
        # Save the data to CSV
        save_to_csv(data, args.output)
        print(f"Successfully extracted balance sheet data for {fiscal_quarter}")
        print(f"Output saved to: {args.output}")
        
    except requests.RequestException as e:
        print(f"Error downloading PDF: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error processing PDF: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()