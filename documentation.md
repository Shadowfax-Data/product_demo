# SEC 10Q Report Data Extractor

This tool extracts financial tables from Microsoft's 10Q SEC filings and saves them as CSV files. It specifically targets the following sections:

- Income Statements
- Balance Sheets
- Cash Flows Statements
- Investments
- Stockholders' Equity Statements

## Installation

1. Clone the repository
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - beautifulsoup4
  - requests
  - pandas

## Usage

The script is run from the command line and requires two arguments:

```bash
python sec_extractor.py --url URL --output-dir OUTPUT_DIRECTORY
```

### Arguments

- `--url`: The URL of the Microsoft 10Q SEC filing (must be from microsoft.gcs-web.com domain)
- `--output-dir`: Directory where the CSV files will be saved (will be created if it doesn't exist)

### Example

```bash
python sec_extractor.py \
  --url https://microsoft.gcs-web.com/node/33446/html \
  --output-dir ./output
```

## Output Files

The script generates the following CSV files in the specified output directory:

- `income_statements.csv`: Contains the consolidated income statements
- `balance_sheets.csv`: Contains the consolidated balance sheets
- `cash_flows.csv`: Contains the cash flows statements
- `investments.csv`: Contains the investments data
- `stockholders_equity.csv`: Contains the stockholders' equity statements

## Process Description

1. **URL Validation**: The script first validates that the provided URL is from the microsoft.gcs-web.com domain.

2. **Content Fetching**: The HTML content is fetched using the requests library with appropriate headers to mimic a browser request.

3. **Table Extraction**: For each financial statement:
   - The script searches for section headers in the HTML content
   - Locates the corresponding table within a reasonable proximity
   - Extracts the table data using BeautifulSoup4

4. **Data Cleaning**:
   - Headers are standardized and cleaned
   - Financial numbers are properly formatted
   - Empty rows and columns are removed
   - Special characters and formatting are handled
   - Negative numbers in parentheses are properly converted

5. **CSV Export**:
   - Data is saved to separate CSV files
   - Numbers are formatted with 2 decimal places
   - Proper UTF-8 encoding is used
   - Empty cells are handled appropriately

## Error Handling

The script includes comprehensive error handling for:
- Invalid URLs
- Network connection issues
- Invalid output directory permissions
- Missing or malformed tables
- Data parsing errors

All errors and warnings are logged with appropriate messages.

## Logging

The script provides detailed logging information about:
- URL fetching status
- Table extraction progress
- File saving operations
- Any errors or warnings encountered

Logs are output to the console with timestamps and appropriate log levels.

## Notes

- The script is specifically designed for Microsoft's 10Q reports and may need modifications for other SEC filings
- Table detection is based on common header patterns in Microsoft's 10Q reports
- The script handles various financial number formats including parentheses for negative numbers
- All financial values are standardized to 2 decimal places in the output CSVs