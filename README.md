# Financial Statement Data Extractor

This tool extracts financial data from Snowflake's quarterly financial statements (10-Q reports) in PDF format. It specifically focuses on extracting and structuring the "Condensed Consolidated Balance Sheets" information into a clean, analyzable CSV format.

## Features

- Downloads financial statement PDFs from provided URLs
- Automatically identifies the balance sheet page
- Extracts tabular data using Camelot
- Processes and validates financial data
- Outputs structured CSV with categorized line items
- Performs data consistency checks
- Handles multiple fiscal quarters

## Requirements

- Python 3.6+
- Required Python packages:
  - camelot-py
  - PyPDF2
  - pandas
  - numpy
  - requests

## Installation

The script requires Camelot and its dependencies to be installed. Camelot is already installed in the environment.

## Usage

```bash
python extract_financials.py <pdf_url> --output <output_csv_path>
```

### Arguments

- `pdf_url`: URL of the financial statement PDF to process
- `--output`: Path where the output CSV file should be saved

### Example

```bash
python extract_financials.py https://s26.q4cdn.com/463892824/files/doc_financials/2025/q1/Snowflake-Q1-FY25-10Q.pdf --output q1_fy2025_balance_sheet.csv
```

## Output Format

The script generates a CSV file with the following columns:

- `fiscal_quarter`: The fiscal quarter identifier (e.g., "Q1 FY2025")
- `category`: The balance sheet category (e.g., "Assets", "Liabilities")
- `line_item`: The specific financial line item
- `amount`: The monetary value in dollars
- `is_total`: Boolean indicating whether the line item is a subtotal or total

## Data Processing Steps

1. **PDF Download**: Downloads the financial statement PDF to a temporary location

2. **Page Identification**: 
   - Searches through the PDF to find the balance sheet page
   - Identifies the page by looking for key phrases and typical balance sheet items
   - Extracts fiscal quarter information

3. **Table Extraction**:
   - Uses Camelot's lattice mode to extract tables
   - Focuses on the main balance sheet table

4. **Data Processing**:
   - Cleans monetary values
   - Identifies categories and subcategories
   - Detects total and subtotal rows
   - Structures data into the required format

5. **Validation**:
   - Ensures all required categories are present
   - Verifies that total assets equals total liabilities plus equity
   - Checks for data consistency and completeness

## Data Quality Checks

The script performs several validation checks:

- Verifies that all monetary values are valid numbers
- Ensures each line item has a category
- Confirms that the balance sheet balances (assets = liabilities + equity)
- Validates total rows against their components
- Checks for missing or invalid data

## Error Handling

The script includes comprehensive error handling for:

- PDF download issues
- Page identification failures
- Table extraction problems
- Data validation errors
- Data consistency issues

## Limitations

- Assumes the balance sheet follows a standard format
- Requires a clear table structure in the PDF
- May need adjustments for significantly different PDF layouts
- Currently optimized for Snowflake's financial statement format

## Contributing

Feel free to submit issues and enhancement requests!