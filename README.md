# Snowflake Financial Statement Data Extractor

This tool extracts consolidated balance sheet data from Snowflake's quarterly financial statement PDFs and converts them into structured CSV and markdown formats.

## Overview

The tool downloads financial statement PDFs from provided URLs, extracts the consolidated balance sheet tables, processes and validates the data, and outputs the results in both CSV and markdown formats. It's designed to be used as part of a data pipeline for automated financial data extraction.

## Prerequisites

- Python 3.x
- Required Python packages:
  - tabula-py (for PDF table extraction)
  - pandas (for data manipulation)
  - requests (for downloading PDFs)
  - PyPDF2 (for PDF processing)

## Installation

The required packages can be installed using pip:

```bash
pip install tabula-py pandas requests PyPDF2
```

## Usage

The script is run from the command line and accepts two required arguments:

```bash
python3 extract_balance_sheets.py --urls URL1 [URL2 ...] --output OUTPUT_PATH
```

### Arguments

- `--urls`: One or more URLs to Snowflake financial statement PDFs
- `--output`: Path where the output CSV file should be saved

### Example

```bash
python3 extract_balance_sheets.py \
  --urls https://s26.q4cdn.com/463892824/files/doc_financials/2025/q3/efd1579f-72d2-4792-a227-b644f897276e.pdf \
         https://s26.q4cdn.com/463892824/files/doc_financials/2025/q2/Q2-FY25-10-Q.pdf \
         https://s26.q4cdn.com/463892824/files/doc_financials/2025/q1/Snowflake-Q1-FY25-10Q.pdf \
  --output balance_sheets.csv
```

## Data Processing Steps

1. **PDF Download**
   - Downloads PDFs from provided URLs to temporary directory
   - Implements error handling for failed downloads
   - Cleans up temporary files after processing

2. **Table Extraction**
   - Uses tabula-py to locate and extract consolidated balance sheet tables
   - Implements smart detection of balance sheet tables based on content
   - Handles multi-page tables and concatenates them appropriately

3. **Data Cleaning**
   - Removes duplicate and redundant columns
   - Standardizes column names and formats
   - Handles various number formats (parentheses for negatives, currency symbols)
   - Categorizes accounts into Assets, Liabilities, and Equity sections
   - Validates data consistency across quarters

4. **Output Generation**
   - Creates a structured CSV file with:
     - Quarter information as the first column
     - Standardized account names
     - Properly formatted numerical values
   - Generates markdown tables with:
     - Clear section headers
     - Aligned columns
     - Proper formatting for readability

## Output Files

The script generates three files:

1. `balance_sheets.csv`: Contains the structured balance sheet data
   - Columns: Quarter, Account, Amount
   - Data sorted by quarter and account categories
   - Consistent number formatting

2. `balance_sheets.md`: Contains the same data formatted as markdown tables
   - Organized by quarter
   - Includes section headers for Assets, Liabilities, and Equity
   - Properly aligned columns

3. `README.md`: This documentation file

## Data Validation

The script performs several validation checks:

- Ensures all required sections (Assets, Liabilities, Equity) are present
- Verifies that total assets match total liabilities plus equity
- Checks for consistency in account names across quarters
- Validates numerical data formats and signs

## Error Handling

The script includes comprehensive error handling for:

- Failed PDF downloads
- Table extraction issues
- Data inconsistencies
- File I/O operations

## Notes

- All monetary values are in thousands of dollars
- Negative values are indicated with parentheses in the output
- The script is designed to work with Snowflake's standard financial statement format
- Temporary files are automatically cleaned up after processing

## Limitations

- The script is specifically designed for Snowflake's financial statement format
- PDF tables must be in a recognizable format for tabula-py to extract
- Internet connection required for downloading PDFs