# Snowflake Financial Statement Data Extractor

This tool extracts consolidated balance sheet data from Snowflake's quarterly financial statements (10-Q) and converts it into a structured CSV format. It's designed to handle Snowflake's financial PDFs consistently and produce clean, validated output.

## Features

- Automatic download of financial statement PDFs from URLs
- Smart detection of consolidated balance sheet pages
- Robust table extraction using both lattice and stream parsing methods
- Comprehensive data cleaning and validation
- Consistent output format with standardized fiscal quarters
- Detailed error handling and progress reporting

## Requirements

- Python 3.x
- Required Python packages:
  - camelot-py
  - pandas
  - PyPDF2
  - requests
  - numpy

## Installation

The script requires several Python packages. Install them using pip:

```bash
pip install camelot-py pandas PyPDF2 requests numpy
```

## Usage

The script is run from the command line and requires two main parameters:
- The URL of the financial statement PDF
- The output path for the CSV file

Basic usage:

```bash
python extract_financials.py <pdf_url> --output <output_path.csv>
```

Example:

```bash
python extract_financials.py https://s26.q4cdn.com/463892824/files/doc_financials/2025/q1/Snowflake-Q1-FY25-10Q.pdf --output /path/to/output/q1_fy25_balance_sheet.csv
```

Optional parameters:
- `--tmp-dir`: Directory for temporary files (default: /tmp)

## Output Format

The script produces a CSV file with the following columns:

1. `fiscal_quarter`: The fiscal quarter (e.g., "Q1 FY2025")
2. `category`: The balance sheet category (e.g., "Assets", "Liabilities")
3. `line_item`: The specific financial line item
4. `amount`: The monetary value in thousands (as integers)

Sample output:

```csv
fiscal_quarter,category,line_item,amount
Q1 FY2025,Assets,Cash and cash equivalents,1234567
Q1 FY2025,Assets,Short-term investments,2345678
...
```

## Data Processing Steps

1. **PDF Download**: Downloads the financial statement PDF from the provided URL

2. **Page Detection**: Identifies the specific page containing the consolidated balance sheet using intelligent text matching

3. **Page Extraction**: Extracts the relevant page to a separate PDF for focused processing

4. **Table Extraction**: Uses Camelot to extract tabular data, trying both lattice and stream parsing methods

5. **Data Cleaning**:
   - Removes empty rows and columns
   - Standardizes date formats
   - Cleans up whitespace and special characters
   - Converts monetary values to integers
   - Identifies and categorizes line items
   - Formats fiscal quarters consistently

6. **Validation**:
   - Ensures all required columns are present
   - Validates numeric data
   - Checks for data completeness
   - Verifies category assignments

## Error Handling

The script includes comprehensive error handling for common issues:
- PDF download failures
- Page detection failures
- Table extraction issues
- Data validation errors

Each error provides a clear message to help diagnose and resolve the issue.

## Limitations

- The script is specifically designed for Snowflake's financial statement format
- Requires a consistent table structure in the PDF
- Assumes amounts are in thousands of dollars
- PDF must be text-searchable (not scanned images)

## Contributing

Feel free to submit issues and enhancement requests. Follow these steps to contribute:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Testing Results

The script has been successfully tested with multiple Snowflake financial statements:

### Q1 FY2025 (April 30, 2024)

Key metrics extracted:
- Cash and cash equivalents: $1,330,411,000
- Short-term investments: $2,200,935,000
- Total assets: $7,298,018,000
- Total liabilities: $2,730,326,000

### Q2 FY2025 (July 31, 2024)

Key metrics extracted:
- Cash and cash equivalents: $1,282,045,000
- Short-term investments: $1,948,462,000
- Total assets: $6,943,886,000
- Total liabilities: $2,806,298,000

The extraction process maintained data integrity and consistency across both reports, with proper handling of:
- Comparative periods (current quarter vs. previous fiscal year end)
- Category classifications
- Line item descriptions
- Monetary values (all in thousands)

## License

This project is licensed under the terms of the LICENSE file included in the repository.