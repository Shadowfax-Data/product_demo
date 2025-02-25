# Caltrain Schedule Parser

This project provides a Python script that downloads and parses the Caltrain schedule PDF into a structured CSV format. The script handles the complexities of PDF table extraction and data cleaning to produce a reliable dataset of train schedules.

## Overview

The script performs the following operations:
1. Downloads the Caltrain schedule PDF from the official website
2. Splits the PDF into northbound and southbound sections
3. Extracts schedule tables using the Camelot library
4. Cleans and transforms the data into a structured format
5. Validates the data for consistency and correctness
6. Exports the cleaned data to a CSV file

## Implementation Details

### PDF Processing
- Uses `requests` library to download the PDF
- Employs `PyPDF2` to analyze and split the PDF into directional sections
- Utilizes `camelot-py` with the 'lattice' flavor for accurate table extraction

### Data Extraction and Cleaning
The script implements several key data processing functions:

1. **Direction Identification**
   - Analyzes page content to identify northbound and southbound schedules
   - Tags each schedule entry with the appropriate direction

2. **Time Standardization**
   - Cleans and standardizes time formats
   - Handles various time formats (AM/PM)
   - Validates time sequence for each train

3. **Station Name Standardization**
   - Removes unnecessary suffixes (e.g., "Station", "Transit Center")
   - Standardizes common station names
   - Ensures consistency across the dataset

4. **Train Number Extraction**
   - Extracts train numbers from table headers
   - Validates numeric values
   - Maintains consistency across schedule entries

### Data Validation
The script includes comprehensive validation checks:
- Ensures all required columns are present
- Verifies data completeness (no null values)
- Validates direction values
- Checks time sequence consistency
- Verifies train number format
- Ensures station names are standardized

## Output Format

The resulting CSV file contains four columns:
- `direction`: Either "Northbound" or "Southbound"
- `train_number`: The unique identifier for each train
- `station`: The standardized station name
- `time`: The arrival/departure time in "HH:MM AM/PM" format

## Usage

To run the script:
```bash
python3 caltrain_schedule_parser.py
```

The script will:
1. Create a `data` directory if it doesn't exist
2. Download the PDF to `data/caltrain_schedule.pdf`
3. Process the schedule
4. Save the results to `data/caltrain_schedule.csv`

## Dependencies

- Python 3.x
- requests
- PyPDF2
- camelot-py
- pandas
- pathlib

## Error Handling

The script includes robust error handling for:
- PDF download failures
- Table extraction issues
- Data validation errors
- File system operations

## Data Quality Assurance

The implementation includes multiple layers of data quality checks:
1. Initial validation of extracted tables
2. Data cleaning and standardization
3. Comprehensive validation of the final dataset
4. Statistical summaries for verification

The resulting CSV file provides a clean, structured, and validated dataset suitable for further analysis or integration into other systems.