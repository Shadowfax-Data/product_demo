# Caltrain Schedule Parser

This project downloads and parses the Caltrain schedule from their official PDF timetable, converting it into a structured CSV format for easier data analysis and integration.

## Project Structure

```
.
├── parse_caltrain.py    # Main Python script for PDF parsing
├── caltrain_schedule.csv # Output file with parsed schedule data
└── README.md            # Project documentation
```

## Implementation Details

### Data Processing Pipeline

1. **PDF Download**
   - Downloads the schedule PDF from Caltrain's official website
   - Implements error handling for failed downloads
   - Automatically cleans up the PDF file after processing

2. **Table Extraction**
   - Uses `tabula-py` to extract tables from the PDF
   - Processes all pages of the document
   - Uses lattice mode for better table structure recognition

3. **Data Cleaning and Validation**
   - **Train Number Validation**
     - Ensures train numbers are numeric
     - Handles both integer and float formats
     - Strips any extra whitespace or characters

   - **Time Format Standardization**
     - Validates time format (HH:MM or H:MM)
     - Cleans and standardizes time strings
     - Removes invalid time entries
     - Uses regex pattern matching for validation

   - **Station Name Processing**
     - Removes empty station entries
     - Strips whitespace from station names
     - Maintains original station naming convention

4. **Data Transformation**
   - Combines data from multiple tables into a unified structure
   - Creates a consistent [train_number, station, time] format
   - Sorts entries by train number and time
   - Removes duplicate entries

## Output Format

The resulting CSV file (`caltrain_schedule.csv`) contains three columns:
- `train_number`: The unique identifier for each train
- `station`: The name of the station
- `time`: The scheduled time in HH:MM format

## Data Statistics
- Total schedule entries: 202
- Multiple train types included (regular and express services)
- Covers stations from San Francisco to Gilroy

## Usage

To run the parser:

```bash
python parse_caltrain.py
```

The script will:
1. Download the latest schedule PDF
2. Process and clean the data
3. Generate `caltrain_schedule.csv`
4. Display a summary of the processed data

## Dependencies

- Python 3.x
- requests
- tabula-py
- pandas
- re (built-in)
- pathlib (built-in)
- datetime (built-in)

## Error Handling

The script includes comprehensive error handling for:
- PDF download failures
- Table extraction issues
- Data validation errors
- File operations
- Automatic cleanup of temporary files