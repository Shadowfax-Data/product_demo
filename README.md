# Snowflake Financial Statement Data Extraction

This project extracts consolidated balance sheet information from Snowflake's financial statements (10-K and 10-Q reports) and compiles the data into a structured CSV format.

## Files

- `snowflake_financial_extractor.py`: Python script for downloading and processing financial statements
- `snowflake_balance_sheets.csv`: Output file containing the extracted balance sheet data

## Data Sources

The script processes the following financial statements:
- FY24 10-K (Q4): January 31, 2024
- FY25 Q3 10-Q: October 31, 2024
- FY25 Q2 10-Q: July 31, 2024
- FY25 Q1 10-Q: April 30, 2024

## Implementation Details

### Data Extraction Process

1. **PDF Download**
   - Uses the `requests` library to download PDFs from Snowflake's investor relations site
   - Implements retry logic with exponential backoff for reliability
   - Verifies file integrity after download
   - Saves files to the `/tmp` directory with standardized naming
   - Handles network errors and incomplete downloads gracefully

2. **Table Extraction**
   - Uses `tabula-py` library to extract tables from PDFs
   - Implements multiple extraction methods (lattice and stream) for better accuracy
   - Uses intelligent page detection with keyword matching
   - Handles split tables across multiple pages
   - Preserves hierarchical relationships in line items
   - Uses a scoring system to identify the correct balance sheet table
   - Extracts both current and prior period data

3. **Data Cleaning**
   - Standardizes column names and data types
   - Handles special characters and formatting in numeric values
   - Processes parentheses for negative values
   - Converts between different units (thousands/millions)
   - Combines split cells and handles multi-column values
   - Removes header rows and empty entries
   - Normalizes line item descriptions for consistency
   - Preserves original formatting where significant

4. **Data Validation**
   - Performs comprehensive balance sheet equation checks
   - Validates period-over-period consistency
   - Checks for missing required line items
   - Validates numeric data types and ranges
   - Verifies date consistency across statements
   - Identifies potential data quality issues
   - Logs validation results for review
   - Cross-references between current and prior periods

### Output Data Structure

The CSV file contains the following columns:
- `line_item`: Balance sheet line item description
- `amount`: Monetary value in USD
- `period_end_date`: Statement period end date
- `source_file`: Source PDF filename

## Usage

Run the script:
```bash
python3 snowflake_financial_extractor.py
```

The script will:
1. Download the required PDFs
2. Extract and process the balance sheet data
3. Save the results to `snowflake_balance_sheets.csv`
4. Display validation results and data quality checks

## Dependencies

- Python 3.x
- pandas
- tabula-py
- PyPDF2
- requests
- numpy

## Data Quality Notes

- All monetary values are in USD
- Prior period comparisons are included
- Missing values are marked as empty in the CSV
- Data validation checks ensure consistency across periods

## Error Handling and Limitations

### Error Handling
- Network connectivity issues during PDF downloads
- PDF parsing and extraction failures
- Table structure variations
- Data type conversion errors
- File system operations
- Validation failures

### Limitations
- Requires specific PDF formatting for optimal extraction
- May need adjustments if report layout changes significantly
- Assumes consistent naming conventions for line items
- Limited to balance sheet data (does not extract income statement or cash flow)
- PDF quality affects extraction accuracy

### Known Issues
- Complex tables spanning multiple pages may require manual verification
- Footnote references in line items might be truncated
- Some formatting variations between quarterly and annual reports
- Unit conversion edge cases in certain historical data

## Future Improvements

Potential enhancements for future versions:
- Support for additional financial statements (income statement, cash flow)
- Enhanced data visualization capabilities
- Automated trend analysis
- API integration for direct data access
- Support for additional file formats
- Automated testing framework
- Machine learning-based table detection
- Interactive data validation interface