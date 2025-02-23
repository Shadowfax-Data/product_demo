# Snowflake Financial Statement Data Extraction

This repository contains a Python script for extracting consolidated balance sheet data from Snowflake's financial statements (10-K and 10-Q reports) in PDF format.

## Overview

The script `extract_financials.py` is designed to:
1. Download financial statement PDFs from provided URLs
2. Extract consolidated balance sheet tables using Tabula
3. Clean and standardize the extracted data
4. Combine data from multiple statements into a single CSV file

## Requirements

- Python 3.12+
- Required packages:
  - tabula-py (2.10.0+)
  - PyPDF2 (3.0.1+)
  - pandas

## Usage

```bash
./extract_financials.py URL1 [URL2 ...] --output OUTPUT_CSV
```

Example:
```bash
./extract_financials.py \
  "https://s26.q4cdn.com/463892824/files/doc_financials/2024/q4/Snowflake-FY24-10K.pdf" \
  "https://s26.q4cdn.com/463892824/files/doc_financials/2025/q3/efd1579f-72d2-4792-a227-b644f897276e.pdf" \
  "https://s26.q4cdn.com/463892824/files/doc_financials/2025/q2/Q2-FY25-10-Q.pdf" \
  "https://s26.q4cdn.com/463892824/files/doc_financials/2025/q1/Snowflake-Q1-FY25-10Q.pdf" \
  --output snowflake_balance_sheets.csv
```

## Data Extraction Process

1. **PDF Download**:
   - Downloads PDFs from provided URLs to a temporary directory
   - Validates that downloaded files are valid PDFs
   - Implements retry mechanism for failed downloads
   - Cleans up temporary files after processing

2. **Table Identification**:
   - Scans PDF pages for balance sheet keywords
   - Uses multiple extraction methods to find the best table
   - Scores tables based on:
     - Presence of balance sheet title
     - Number of balance sheet content keywords
     - Number of numeric values
     - Column alignment and structure
     - Date presence and format
   - Handles both landscape and portrait orientations

3. **Data Cleaning**:
   - Standardizes line item names using predefined mappings
   - Converts numeric values to consistent format (thousands USD)
   - Handles parentheses for negative numbers
   - Removes non-balance sheet rows and footnotes
   - Validates data using accounting equation checks
   - Performs cross-period consistency checks
   - Handles currency symbols and scale indicators

4. **Data Validation**:
   - Verifies Assets = Liabilities + Shareholders' Equity
   - Checks for required line items (e.g., Total Assets, Total Liabilities)
   - Validates date sequence across statements
   - Ensures consistent scale across all values
   - Flags suspicious variations between periods
   - Generates warnings for potential data quality issues

5. **Data Consolidation**:
   - Combines data from multiple statements
   - Standardizes column names across files
   - Sorts by statement date and line item
   - Handles overlapping periods in different filings
   - Maintains audit trail with source URLs
   - Ensures consistent data types across all fields

## Output Format

The script generates a CSV file with the following columns:
- `statement_date`: The date of the financial statement (YYYY-MM-DD)
- `filing_type`: Type of filing (10-K or 10-Q)
- `line_item`: Standardized balance sheet line item name
- `amount`: Value in thousands of USD (numeric)
- `category`: Classification (Asset, Liability, or Equity)
- `source_url`: Original PDF URL for traceability
- `extraction_date`: Timestamp of data extraction
- `validation_status`: Indicates if the entry passed all validation checks

## Limitations and Known Issues

1. The script currently focuses on consolidated balance sheets only
2. Some line items may be missed if they use non-standard formatting
3. The script assumes a specific table structure in the PDFs
4. Date extraction from filenames assumes Snowflake's fiscal year pattern
5. Processing time increases with PDF complexity and file size
6. Memory usage can be significant for large PDFs or many files
7. Some PDF security settings may prevent automated extraction

## Error Handling

The script implements comprehensive error handling for:
1. Network issues during PDF downloads
   - Connection timeouts
   - Invalid URLs
   - Server errors
2. PDF processing errors
   - Invalid PDF format
   - Encrypted files
   - Missing pages
3. Data validation failures
   - Accounting equation mismatches
   - Missing required fields
   - Inconsistent data formats
4. File system operations
   - Insufficient permissions
   - Disk space issues
   - File access conflicts

## Future Improvements

1. Add support for income statements and cash flow statements
2. Improve table detection for non-standard formats
3. Enhance validation checks for data quality
4. Support for different fiscal year patterns
5. Add support for more financial statement formats
6. Implement parallel processing for multiple PDFs
7. Add machine learning-based table detection
8. Create a web interface for file uploads
9. Support for incremental updates to existing datasets
10. Add automated regression testing with sample PDFs