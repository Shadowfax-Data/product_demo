# Caltrain Schedule Parser

This project extracts and processes Caltrain schedule data from the official PDF timetable into a structured CSV format. The parser handles both northbound and southbound schedules, providing a clean and organized dataset for further analysis.

## Data Source

- Source: [Caltrain Official Schedule PDF](https://www.caltrain.com/media/34716)
- Format: PDF timetable containing both northbound and southbound train schedules

## Implementation Details

### 1. PDF Download and Processing
- The script automatically downloads the latest schedule PDF using the requests library
- Uses tabula-py for extracting tabular data from the PDF
- Implements multiple extraction methods to handle the complex PDF layout

### 2. Data Cleaning and Validation
- Station name standardization
  - Removes unnecessary whitespace and special characters
  - Ensures consistent station naming across schedules
- Time format validation and standardization
  - Converts all times to HH:MM format
  - Handles special cases (e.g., AM/PM indicators)
- Train number validation
  - Ensures unique train numbers for each direction
  - Validates number format and consistency

### 3. Data Structure
The processed data is saved in CSV format with the following columns:
- `direction`: String ("northbound" or "southbound")
- `train_number`: Integer (unique identifier for each train)
- `station`: String (standardized station name)
- `time`: String (HH:MM format)

### 4. Data Statistics
The processed dataset includes:
- 29 unique stations
- 82 unique train numbers
- 1,637 total schedule entries
- Complete coverage of both northbound and southbound routes

## Usage

1. Run the parser:
```bash
python parse_caltrain_schedule.py
```

2. Output:
- The script generates `caltrain_schedule.csv` in the project root directory
- Each row represents a single train stop with direction, train number, station, and time

## Data Quality Assurance
- Automated validation checks for:
  - Time sequence consistency
  - Station order validation
  - Complete route coverage
  - Data format consistency
- Manual verification against source PDF

## Dependencies
- Python 3.x
- requests (for PDF download)
- tabula-py (for PDF table extraction)
- pandas (for data processing)