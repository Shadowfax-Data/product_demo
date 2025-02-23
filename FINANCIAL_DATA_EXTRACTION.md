# Snowflake Financial Statement Data Extraction

This document describes the process and tools used to extract financial data from Snowflake's quarterly financial statements, specifically focusing on the Condensed Consolidated Balance Sheets.

## Overview

The data extraction process uses a custom Python script (`snowflake_financials_extractor.py`) to automatically download, process, and extract tabular data from Snowflake's quarterly financial statements (10-Q reports). The script handles the entire pipeline from PDF download to structured CSV output.

## Requirements

- Python 3.7+
- Required Python packages:
  - camelot-py
  - pandas
  - requests
  - PyPDF2

## Usage

The script can be run from the command line with the following syntax:

```bash
python snowflake_financials_extractor.py --url <pdf_url> --output <output_csv_path>
```

Example:
```bash
python snowflake_financials_extractor.py \
  --url https://s26.q4cdn.com/463892824/files/doc_financials/2025/q1/Snowflake-Q1-FY25-10Q.pdf \
  --output snowflake_q1_fy25_balance_sheet.csv
```

## Data Extraction Process

1. **PDF Download**
   - The script downloads the specified PDF file to a temporary location
   - Validates the PDF file integrity and accessibility

2. **Balance Sheet Page Identification**
   - Scans through PDF pages to locate the Condensed Consolidated Balance Sheets
   - Extracts the relevant page to a separate PDF for focused processing

3. **Table Extraction**
   - Uses Camelot library to extract tabular data
   - Handles complex table layouts and merged cells
   - Processes both numerical and text data

4. **Data Cleaning and Structuring**
   - Normalizes extracted data
   - Identifies categories and line items
   - Marks total rows
   - Formats amounts consistently

## Output Format

The script generates a CSV file with the following columns:

- `fiscal_quarter`: The fiscal quarter of the report (e.g., "Q1 FY25")
- `category`: The balance sheet category (e.g., "Assets", "Liabilities")
- `line_item`: The specific line item description
- `amount`: The monetary value (in thousands of dollars)
- `is_total`: Boolean flag indicating whether the row represents a total/subtotal

## Data Validation

The script performs several validation checks:

1. Ensures all required columns are present
2. Validates numerical data in amount fields
3. Checks for logical consistency in totals
4. Verifies category and line item relationships

## Known Limitations

- The script is specifically designed for Snowflake's financial statement format
- PDF formatting changes may require script adjustments
- Complex table layouts might require manual verification

## Troubleshooting

Common issues and solutions:

1. **PDF Download Failures**
   - Check URL accessibility
   - Verify network connection
   - Ensure sufficient disk space

2. **Table Extraction Issues**
   - Verify PDF file integrity
   - Check for format changes in source documents
   - Adjust table extraction parameters if needed

## Sample Output

Example of extracted data structure:

```csv
fiscal_quarter,category,line_item,amount,is_total
Q1 FY25,Assets,Cash and cash equivalents,1234567,false
Q1 FY25,Assets,Short-term investments,2345678,false
Q1 FY25,Assets,Total current assets,3580245,true
```

## Support

For issues or questions about the extraction process, please refer to the script documentation or raise an issue in the repository.