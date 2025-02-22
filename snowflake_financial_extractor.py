#!/usr/bin/env python3

import os
import re
import requests
import pandas as pd
import numpy as np
import tabula
import PyPDF2
from typing import List, Dict, Optional, Tuple, Union
from urllib.parse import urlparse
from datetime import datetime

class FinancialPDFDownloader:
    def __init__(self, output_dir: str = "/tmp"):
        self.output_dir = output_dir
        self.pdf_urls = [
            "https://s26.q4cdn.com/463892824/files/doc_financials/2024/q4/Snowflake-FY24-10K.pdf",
            "https://s26.q4cdn.com/463892824/files/doc_financials/2025/q3/efd1579f-72d2-4792-a227-b644f897276e.pdf",
            "https://s26.q4cdn.com/463892824/files/doc_financials/2025/q2/Q2-FY25-10-Q.pdf",
            "https://s26.q4cdn.com/463892824/files/doc_financials/2025/q1/Snowflake-Q1-FY25-10Q.pdf"
        ]
        self.downloaded_files: List[str] = []

    def get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL and ensure it ends with .pdf"""
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        return filename

    def download_pdfs(self) -> List[str]:
        """Download all PDFs to the output directory"""
        for url in self.pdf_urls:
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                filename = self.get_filename_from_url(url)
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                self.downloaded_files.append(filepath)
                print(f"Successfully downloaded: {filename}")
                
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {url}: {str(e)}")
                continue
        
        return self.downloaded_files

class PDFProcessor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_reader = PyPDF2.PdfReader(pdf_path)
        self.period_end_date: Optional[str] = None
        self.extracted_data: Optional[pd.DataFrame] = None

    def find_balance_sheet_page(self) -> Optional[int]:
        """Find the page number containing the consolidated balance sheet"""
        for i, page in enumerate(self.pdf_reader.pages):
            text = page.extract_text().lower()
            if "consolidated balance sheet" in text and "assets" in text:
                return i
        return None

    def extract_period_end_date(self, page_text: str) -> Optional[str]:
        """Extract the period end date from the balance sheet page"""
        date_patterns = [
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
            r"\d{1,2}/\d{1,2}/\d{4}"
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                try:
                    date_str = matches[0]
                    if '/' in date_str:
                        date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    else:
                        date_obj = datetime.strptime(date_str, '%B %d, %Y')
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        return None

    def extract_balance_sheet(self) -> Optional[pd.DataFrame]:
        """Extract the consolidated balance sheet table from the PDF"""
        page_num = self.find_balance_sheet_page()
        if page_num is None:
            print(f"Could not find balance sheet in {self.pdf_path}")
            return None

        # Extract the page text to get the period end date
        page_text = self.pdf_reader.pages[page_num].extract_text()
        self.period_end_date = self.extract_period_end_date(page_text)

        # Try different table extraction methods
        tables = []
        
        # Method 1: Try with lattice mode
        tables.extend(tabula.read_pdf(
            self.pdf_path,
            pages=page_num + 1,  # tabula uses 1-based page numbers
            multiple_tables=True,
            lattice=True,
            guess=False,
            pandas_options={'header': None}
        ))
        
        # Method 2: Try with stream mode if no good tables found
        if not any(isinstance(t, pd.DataFrame) and len(t) > 10 for t in tables):
            tables.extend(tabula.read_pdf(
                self.pdf_path,
                pages=page_num + 1,
                multiple_tables=True,
                stream=True,
                guess=False,
                pandas_options={'header': None}
            ))

        if not tables:
            print(f"No tables found on balance sheet page in {self.pdf_path}")
            return None

        # Find the balance sheet table (the one with the most rows and containing key terms)
        def score_table(df):
            if not isinstance(df, pd.DataFrame) or df.empty:
                return -1
            
            score = len(df)  # Base score is number of rows
            
            # Check for key balance sheet terms
            key_terms = ['assets', 'liabilities', 'equity', 'cash', 'total']
            text = ' '.join(str(val).lower() for val in df.values.flatten())
            score += sum(10 for term in key_terms if term in text)
            
            # Check for numeric values
            num_count = sum(1 for val in df.values.flatten() 
                          if isinstance(val, (int, float)) or 
                          (isinstance(val, str) and any(c.isdigit() for c in val)))
            score += num_count
            
            return score

        # Debug: Print table information
        print("\nFound tables:")
        for i, table in enumerate(tables):
            if isinstance(table, pd.DataFrame):
                print(f"\nTable {i} (Shape: {table.shape}):")
                print(table.head())
                print(f"Score: {score_table(table)}")

        balance_sheet = max(tables, key=score_table)
        
        if balance_sheet.empty:
            print(f"Empty balance sheet table extracted from {self.pdf_path}")
            return None

        print("\nSelected balance sheet table:")
        print(balance_sheet.head())

        # Clean up the table
        # Drop completely empty rows and columns
        balance_sheet = balance_sheet.dropna(how='all').dropna(axis=1, how='all')
        
        # Reset the index
        balance_sheet = balance_sheet.reset_index(drop=True)

        print("\nCleaned balance sheet table:")
        print(balance_sheet.head())

        self.extracted_data = balance_sheet
        return balance_sheet

class DataCleaner:
    def __init__(self):
        self.amount_pattern = re.compile(r'[\$,)]')
        self.expected_columns = {
            'Assets', 'Liabilities', 'stockholders', 'equity', 'Cash', 'equivalents',
            'accounts', 'receivable', 'prepaid', 'expenses', 'property', 'equipment'
        }

    def standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names by removing special characters and extra spaces"""
        df.columns = df.columns.str.strip().str.lower()
        df.columns = df.columns.str.replace(r'[^\w\s]', ' ', regex=True)
        df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
        return df

    def clean_amount_string(self, value: str) -> Optional[float]:
        """Convert string amount to float, handling parentheses for negative numbers"""
        if pd.isna(value) or not isinstance(value, str):
            return None
        
        value = value.strip()
        if not value:
            return None

        # Remove $ and commas
        value = self.amount_pattern.sub('', value)
        
        # Handle parentheses (negative numbers)
        is_negative = '(' in value and ')' in value
        value = value.replace('(', '').replace(')', '')
        
        try:
            amount = float(value)
            return -amount if is_negative else amount
        except ValueError:
            return None

    def convert_amounts_to_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert amount columns to numeric values"""
        for col in df.columns:
            if col != 'line_item':  # Skip the line item column
                df[col] = df[col].apply(self.clean_amount_string)
        return df

    def identify_balance_sheet_sections(self, df: pd.DataFrame) -> Dict[str, List[int]]:
        """Identify the rows that belong to different sections of the balance sheet"""
        sections = {
            'assets': [],
            'liabilities': [],
            'equity': []
        }
        
        for idx, row in df.iterrows():
            row_text = ' '.join(str(val).lower() for val in row.values)
            if 'total assets' in row_text:
                sections['assets'].append(idx)
            elif 'total liabilities' in row_text:
                sections['liabilities'].append(idx)
            elif 'total stockholders' in row_text and 'equity' in row_text:
                sections['equity'].append(idx)
        
        return sections

    def validate_data(self, df: pd.DataFrame, date: str) -> Tuple[bool, List[str]]:
        """Validate the cleaned data for common issues"""
        issues = []
        
        # Check for missing values
        missing_pct = df['amount'].isnull().mean() * 100
        if missing_pct > 20:  # More than 20% missing values
            issues.append(f"High percentage of missing values: {missing_pct:.1f}%")

        # Check for negative values in typically positive accounts
        positive_accounts = ['cash', 'equivalents', 'receivable', 'prepaid']
        for idx, row in df.iterrows():
            line_item = str(row['line_item']).lower()
            if any(term in line_item for term in positive_accounts):
                if pd.notna(row['amount']) and row['amount'] < 0:
                    issues.append(f"Negative value found in {line_item}: {row['amount']}")

        # Validate balance sheet equation: Assets = Liabilities + Equity
        # Group by period_end_date to validate each period separately
        for period in df['period_end_date'].unique():
            period_data = df[df['period_end_date'] == period]
            try:
                # Find total assets row
                total_assets_row = period_data[
                    period_data['line_item'].str.contains('total assets', case=False, na=False)
                ].iloc[0]
                
                # Find total liabilities and equity row
                total_le_row = period_data[
                    period_data['line_item'].str.contains('total liabilities and stockholders', case=False, na=False)
                ].iloc[0]
                
                total_assets = total_assets_row['amount']
                total_le = total_le_row['amount']
                
                if pd.notna(total_assets) and pd.notna(total_le):
                    if not np.isclose(total_assets, total_le, rtol=0.01):
                        issues.append(
                            f"Balance sheet equation doesn't balance for period {period}: "
                            f"Assets ({total_assets:,.0f}) ≠ "
                            f"Liabilities + Equity ({total_le:,.0f})"
                        )
            except (IndexError, KeyError):
                issues.append(f"Could not verify balance sheet equation for period {period}")

        return len(issues) == 0, issues

    def process_balance_sheet(self, df: pd.DataFrame, date: str) -> Tuple[pd.DataFrame, List[str]]:
        """Process and clean the balance sheet data"""
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Identify the first column as line items
        df = df.rename(columns={df.columns[0]: 'line_item'})
        
        # Clean up the data structure
        # The table has alternating columns for current and prior period
        # We need to combine them properly
        current_period_data = []
        prior_period_data = []
        
        # Function to combine adjacent columns into a single value
        def combine_amount_columns(row, start_col, num_cols=2):
            amount = None
            for col in range(start_col, min(start_col + num_cols, len(row))):
                if pd.notna(row[col]):
                    val = str(row[col]).strip()
                    # If this is a dollar sign and the next column has the number
                    if val == '$' and col + 1 < len(row) and pd.notna(row[col + 1]):
                        val = f"${str(row[col + 1]).strip()}"
                    # If this looks like a number
                    if val.startswith('$') or val.replace(',', '').replace('(', '').replace(')', '').strip().isdigit():
                        amount = val
                        break
            return amount
        
        for idx, row in df.iterrows():
            line_item = row['line_item']
            if pd.isna(line_item) or str(line_item).strip() == '':
                continue
            
            # Clean up line item
            line_item = str(line_item).strip()
            if line_item.lower() in ['assets', 'liabilities', "stockholders' equity"]:
                continue
            
            # Extract amounts for current and prior periods
            current_amount = combine_amount_columns(row, 1)
            prior_amount = combine_amount_columns(row, 4)
            
            # Only add rows that have at least one amount
            if current_amount is not None:
                current_period_data.append({
                    'line_item': line_item,
                    'amount': current_amount
                })
            
            if prior_amount is not None:
                prior_period_data.append({
                    'line_item': line_item,
                    'amount': prior_amount
                })
        
        # Create clean DataFrames for each period
        current_df = pd.DataFrame(current_period_data)
        prior_df = pd.DataFrame(prior_period_data)
        
        # Convert amounts to numeric values
        current_df['amount'] = current_df['amount'].apply(self.clean_amount_string)
        prior_df['amount'] = prior_df['amount'].apply(self.clean_amount_string)
        
        # Add period information
        current_df['period_end_date'] = date
        prior_df['period_end_date'] = '2024-01-31'  # All prior periods in these statements are as of Jan 31, 2024
        
        # Combine the data
        result_df = pd.concat([current_df, prior_df], ignore_index=True)
        
        # Drop rows where both line_item and amount are null
        result_df = result_df.dropna(how='all', subset=['line_item', 'amount'])
        
        # Validate the data
        is_valid, issues = self.validate_data(result_df, date)
        if not is_valid:
            print(f"Warning: Data validation issues found for {date}:")
            for issue in issues:
                print(f"- {issue}")
        
        return result_df, issues

def main():
    # Download PDFs
    downloader = FinancialPDFDownloader()
    downloaded_files = downloader.download_pdfs()
    
    # Initialize data cleaner
    cleaner = DataCleaner()
    
    # Process each PDF
    all_data = []
    all_issues = []
    
    for pdf_path in downloaded_files:
        print(f"\nProcessing {pdf_path}")
        processor = PDFProcessor(pdf_path)
        balance_sheet = processor.extract_balance_sheet()

        if balance_sheet is not None and processor.period_end_date:
            print(f"Successfully extracted balance sheet for period ending {processor.period_end_date}")

            # Clean and validate the data
            cleaned_df, issues = cleaner.process_balance_sheet(balance_sheet, processor.period_end_date)

            # Add source file information
            cleaned_df['source_file'] = os.path.basename(pdf_path)

            all_data.append(cleaned_df)

            if issues:
                all_issues.append({
                    'file': os.path.basename(pdf_path),
                    'date': processor.period_end_date,
                    'issues': issues
                })
        else:
            print(f"Failed to extract balance sheet from {pdf_path}")

    print(f"\nProcessed {len(all_data)} balance sheets successfully")

    if all_issues:
        print("\nData validation issues found:")
        for issue_set in all_issues:
            print(f"\nFile: {issue_set['file']} (Period: {issue_set['date']})")
            for issue in issue_set['issues']:
                print(f"- {issue}")
    else:
        print("\nNo data validation issues found")

    # Combine all data and save to CSV
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by period end date and line item
        final_df = final_df.sort_values(['period_end_date', 'line_item'])
        
        # Format amounts with proper precision
        final_df['amount'] = final_df['amount'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '')
        
        # Add metadata as a comment in the CSV
        output_path = '/workspace/snowflake_balance_sheets.csv'
        with open(output_path, 'w') as f:
            f.write("# Snowflake Inc. Consolidated Balance Sheets\n")
            f.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# Source: SEC Filings (10-K and 10-Q reports)\n")
            f.write("# All amounts in thousands (000s) of US dollars\n")
            f.write("#\n")
            final_df.to_csv(f, index=False)
        
        print(f"\nSaved balance sheet data to: {output_path}")
        
        # Display summary statistics
        print("\nData Summary:")
        print(f"Total periods: {final_df['period_end_date'].nunique()}")
        print(f"Date range: {final_df['period_end_date'].min()} to {final_df['period_end_date'].max()}")
        print(f"Total line items: {len(final_df['line_item'].unique())}")
        print("\nSample of extracted data:")
        print(final_df.head(10))
        
        # Verify the CSV was written correctly
        try:
            test_df = pd.read_csv(output_path, comment='#')
            print(f"\nVerified CSV file was written successfully with {len(test_df)} rows")
        except Exception as e:
            print(f"\nWarning: Error verifying CSV file: {str(e)}")

if __name__ == "__main__":
    main()