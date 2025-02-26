# Caltrain Schedule PDF Parsing Process

This document describes the process of extracting and transforming Caltrain schedule data from a PDF into a structured CSV format.

## Overview

The parsing process involves three main steps:
1. PDF Download
2. Table Extraction
3. Data Cleaning and Transformation

## Implementation Details

### 1. PDF Download
- The script downloads the Caltrain schedule PDF from the official URL using the `requests` library
- The PDF is temporarily stored on disk for processing
- After processing, the temporary file is automatically cleaned up

### 2. Table Extraction
The `tabula-py` library is used to extract schedule tables from the PDF with the following approach:
- All pages are processed (`pages='all'`)
- Multiple tables per page are supported (`multiple_tables=True`)
- Each table is processed individually to handle varying layouts

### 3. Data Cleaning and Transformation

The raw extracted data undergoes several cleaning steps:

#### Table Processing
- Empty tables are filtered out
- Station names are extracted from the first column
- Train numbers are identified from numeric column headers
- Data is restructured into a consistent [train_number, station, time] format

#### Data Cleaning
1. **Missing Data Handling**
   - Rows with missing stations or times are removed
   - Empty rows are filtered out

2. **Station Names**
   - Leading/trailing whitespace is removed
   - Generic terms like "station", "stop", "stations" are filtered out
   - Station names are standardized as strings

3. **Train Numbers**
   - Converted to integer format
   - Used for sorting the final dataset

4. **Time Format**
   - Leading/trailing whitespace is removed
   - Preserved in original format (e.g., "4:37a" for 4:37 AM)

## Output Format

The final CSV file contains three columns:
- `train_number`: Integer identifying the train service
- `station`: String name of the station
- `time`: String representing arrival/departure time

Example output:
```csv
train_number,station,time
101,Tamien,4:37a
101,22nd Street,5:55a
101,Bayshore,5:50a
```

## Assumptions and Limitations

1. **Table Structure**
   - First column contains station names
   - Other numeric columns represent train numbers
   - Time format is consistent throughout the PDF

2. **Data Validation**
   - Only processes tables that contain valid train numbers
   - Assumes station names are consistent across tables
   - Times are treated as strings to preserve AM/PM format

3. **Error Handling**
   - Invalid or empty tables are skipped
   - PDF download failures raise exceptions
   - Missing data in critical fields (station, time) results in row removal