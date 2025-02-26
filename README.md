# Caltrain Schedule Parser

This project extracts and processes Caltrain schedule data from the official PDF timetable into a structured CSV format. The parser handles the complex multi-page PDF schedule and converts it into a clean, machine-readable format.

## Overview

The project consists of three main components:
1. A Python script (`parse_schedule.py`) that downloads and processes the PDF
2. The output data file (`caltrain_schedule.csv`)
3. This documentation explaining the process

## Methodology

### 1. Data Acquisition
- The script downloads the official Caltrain schedule PDF using Python's requests library
- Error handling ensures the download process is robust and verifies the PDF content

### 2. PDF Parsing
- Uses tabula-py library to extract tables from each page of the PDF
- Implements page-by-page processing to handle the multi-page schedule format
- Extracts raw tabular data while preserving the schedule structure

### 3. Data Processing and Cleaning

The script performs several cleaning and standardization steps:

#### Time Format Standardization
- Converts various time formats to a consistent 24-hour format
- Handles AM/PM indicators
- Validates time entries for correctness

#### Train Number Processing
- Extracts and validates train numbers
- Ensures consistent numeric format
- Handles special cases and validates against expected patterns

#### Station Name Standardization
- Cleans and standardizes station names
- Removes unnecessary whitespace and special characters
- Ensures consistent naming across all entries

### 4. Data Validation

The processing pipeline includes several validation steps:
- Verifies all required fields are present
- Checks for logical consistency in times
- Validates train numbers against expected patterns
- Ensures station names match known Caltrain stations

## Output Format

The final CSV file contains three columns:
1. `train_number`: The unique identifier for each train
2. `station`: The standardized station name
3. `time`: The arrival/departure time in 24-hour format

## Statistics

The processed dataset includes:
- 1,761 total schedule entries
- 98 unique trains
- 29 distinct stations

## Challenges and Solutions

### 1. PDF Structure Complexity
- **Challenge**: The PDF contains multiple tables per page with varying layouts
- **Solution**: Implemented robust table detection and extraction logic using tabula-py's area detection

### 2. Time Format Variations
- **Challenge**: Times appeared in different formats (AM/PM, merged cells)
- **Solution**: Developed comprehensive time parsing logic to handle all variations

### 3. Data Integrity
- **Challenge**: Ensuring data completeness and accuracy across all pages
- **Solution**: Implemented thorough validation checks and data cleaning procedures

## Usage

To run the parser:

```bash
python parse_schedule.py
```

The script will:
1. Download the latest schedule PDF
2. Process and clean the data
3. Generate the CSV output file

## Dependencies

- Python 3.x
- tabula-py
- pandas
- requests

## Data Quality Assurance

The final dataset has been verified for:
- Completeness of schedule entries
- Correct time sequencing
- Valid train numbers
- Standardized station names
- Proper time formatting