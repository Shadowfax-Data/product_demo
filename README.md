# Financial Statement Data Extractor

This project provides a Python script for extracting financial data from Snowflake's quarterly financial statements (10-Q reports). The script specifically targets the "Condensed Consolidated Balance Sheets" section and converts the data into a structured CSV format for further analysis.

## Features

- Downloads PDF financial statements from provided URLs
- Automatically locates and extracts balance sheet tables
- Performs data validation and cleaning
- Maintains hierarchical structure of financial statements
- Exports clean data to CSV format
- Handles multi-page balance sheets
- Validates numeric values and date formats

## Installation

The script requires Python 3.6+ and the following dependencies:
```bash
pip install requests pdfplumber pandas numpy
```

## Usage

```bash
python extract_financials.py --url <pdf_url> --output <output_csv_path>
```

Example:
```bash
python extract_financials.py \
  --url https://s26.q4cdn.com/463892824/files/doc_financials/2025/q1/Snowflake-Q1-FY25-10Q.pdf \
  --output output/snowflake_balance_sheet_q1_fy25.csv
```

## Data Extraction Process

The script follows a systematic approach to extract and process financial data:

1. **PDF Download**: 
   - Downloads the PDF from the provided URL
   - Saves to a temporary directory for processing

2. **Table Location**:
   - Searches for "Condensed Consolidated Balance Sheets" section
   - Identifies relevant pages through content analysis
   - Handles multi-page tables

3. **Data Extraction**:
   - Extracts text with position information
   - Maintains hierarchical structure (sections and subsections)
   - Processes date headers and financial values

4. **Data Validation**:
   - Validates date formats in column headers
   - Checks numeric values for consistency
   - Identifies and handles outliers
   - Verifies balance sheet equations

5. **Data Cleaning**:
   - Removes currency symbols and formatting
   - Standardizes number formats
   - Cleans and structures labels
   - Maintains proper hierarchical relationships

## Sample Data Analysis

Below is an analysis of the extracted Q1 FY25 balance sheet data:

### Key Financial Metrics (in thousands)

1. **Assets**:
   - Cash and Cash Equivalents: $1,330,411
   - Short-term Investments: $2,200,935
   - Total Current Assets: $4,143,290

2. **Liabilities**:
   - Current Liabilities: $2,428,823
   - Total Liabilities: $2,730,326

3. **Stockholders' Equity**:
   - Additional Paid-in Capital: $9,546,792
   - Total Stockholders' Equity: $4,567,692

### Quarter-over-Quarter Changes

1. **Significant Changes**:
   - Cash and Cash Equivalents decreased by $432,338
   - Accounts Receivable decreased by $581,397
   - Deferred Revenue (current) decreased by $263,063

2. **Balance Sheet Strength**:
   - Current Ratio (Current Assets/Current Liabilities): 1.71
   - Quick Ratio ((Cash + Short-term Investments)/Current Liabilities): 1.45

## Data Quality Measures

The script implements several data quality checks:

1. **Structural Validation**:
   - Ensures proper balance sheet hierarchy
   - Validates section completeness
   - Verifies date format consistency

2. **Numeric Validation**:
   - Outlier detection using IQR method
   - Balance sheet equation verification
   - Consistency checks across periods

3. **Label Standardization**:
   - Hierarchical label structure
   - Consistent formatting
   - Clear parent-child relationships

## Limitations and Considerations

- The script is optimized for Snowflake's financial statement format
- PDF formatting changes may require script adjustments
- Some manual verification recommended for critical financial analysis
- Complex footnotes and annotations are not processed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.