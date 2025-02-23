# Snowflake Financial Statement Data Extraction

This documentation describes the automated process for extracting consolidated balance sheet data from Snowflake's quarterly financial statement PDFs.

## Overview

The `extract_balance_sheets.py` script is a command-line tool that automates the extraction of consolidated balance sheet data from Snowflake's quarterly financial statements. It processes multiple PDF files, extracts tabular data, performs data cleaning and validation, and outputs the results in both CSV and Markdown formats.

## Prerequisites

- Python 3.12 or later
- Required Python packages:
  - tabula-py (2.10.0 or later)
  - PyPDF2
  - pandas
  - requests

## Installation

No installation is required if the prerequisites are met. The script can be run directly from the command line.

## Usage

```bash
python extract_balance_sheets.py [-h] --urls URLS [URLS ...] --output OUTPUT
```

### Arguments

- `--urls`: One or more URLs to Snowflake financial statement PDFs
- `--output`: Path for the output CSV file (the markdown file will be created in the same directory)

### Example

```bash
python extract_balance_sheets.py \
  --urls https://s26.q4cdn.com/463892824/files/doc_financials/2025/q3/efd1579f-72d2-4792-a227-b644f897276e.pdf \
         https://s26.q4cdn.com/463892824/files/doc_financials/2025/q2/Q2-FY25-10-Q.pdf \
  --output /path/to/output/balance_sheets.csv
```

## Process Flow

1. **PDF Download**
   - Downloads PDFs from provided URLs to temporary directory
   - Validates successful downloads and file integrity

2. **Table Extraction**
   - Uses PyPDF2 to analyze PDF content and identify relevant pages
   - Employs Tabula to extract tables using both stream and lattice modes
   - Identifies consolidated balance sheet tables using multiple indicators

3. **Data Cleaning**
   - Standardizes numeric values (removes parentheses, converts to proper format)
   - Handles scale indicators (thousands, millions)
   - Removes duplicate entries and unnecessary whitespace
   - Standardizes column names and row labels

4. **Data Validation**
   - Verifies table structure matches expected balance sheet format
   - Validates numeric values and totals
   - Ensures consistency across different quarterly reports
   - Checks for missing required sections (assets, liabilities, equity)

5. **Output Generation**
   - Creates CSV file with cleaned and validated data
   - Generates markdown tables with proper formatting
   - Includes metadata and source information

## Assumptions and Limitations

1. **PDF Structure**
   - Assumes Snowflake's financial statements follow a consistent format
   - Balance sheet tables are expected to be clearly labeled
   - Numbers are presented in thousands or millions of dollars

2. **Data Format**
   - Negative values are enclosed in parentheses
   - Monetary values use standard US number formatting
   - Column headers include date information

3. **Table Recognition**
   - Balance sheets are identified by specific keywords
   - Tables span multiple pages in some cases
   - Some manual verification may be needed for edge cases

## Error Handling

The script includes comprehensive error handling for:
- Failed PDF downloads
- Inaccessible URLs
- Corrupted PDF files
- Unrecognizable table formats
- Data validation failures
- Output file permission issues

## Output Files

1. **CSV File**
   - Contains cleaned and validated balance sheet data
   - Includes metadata columns (date, fiscal quarter)
   - Uses consistent number formatting
   - Proper quoting and escaping of special characters

2. **Markdown File**
   - Presents data in well-formatted tables
   - Includes headers and explanatory notes
   - Maintains data alignment and readability
   - Contains source information and dates

## Maintenance and Updates

To maintain and update the script:
1. Regularly test with new quarterly reports
2. Update table recognition patterns if format changes
3. Adjust validation rules as needed
4. Monitor for changes in PDF structure or formatting

## Known Issues

1. Very complex table layouts might require manual verification
2. PDF security features could prevent automatic extraction
3. Significant format changes may require script updates

## Contributing

When contributing to this project:
1. Test with multiple PDF versions
2. Maintain existing error handling
3. Document any new assumptions
4. Update validation rules as needed

## License

This tool is provided under the project's license terms. Please refer to the LICENSE file for details.