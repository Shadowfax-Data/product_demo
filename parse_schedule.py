import requests
import tabula
import pandas as pd
from pathlib import Path
import logging
import re
from datetime import datetime
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_pdf(url, output_path):
    """Download PDF file from URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Successfully downloaded PDF to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading PDF: {e}")
        return False

def extract_tables(pdf_path):
    """Extract tables from PDF using tabula."""
    try:
        # Read all pages
        tables = tabula.read_pdf(
            pdf_path,
            pages='all',
            multiple_tables=True,
            guess=True,
            pandas_options={'header': None}
        )
        logger.info(f"Successfully extracted {len(tables)} tables from PDF")
        return tables
    except Exception as e:
        logger.error(f"Error extracting tables from PDF: {e}")
        return None

def clean_train_number(value):
    """Extract and clean train number."""
    if pd.isna(value):
        return None
    # Extract numbers from string
    match = re.search(r'\d+', str(value))
    return int(match.group()) if match else None

def clean_time(value):
    """Clean and standardize time format."""
    if pd.isna(value):
        return None
    
    value = str(value).strip().upper()
    
    # Handle multiple times in one cell (take the first one)
    if len(value) > 10:  # If string is too long, likely contains multiple times
        value = value.split()[0]
    
    # Remove any non-time related text
    value = re.sub(r'[^0-9:APM]', '', value)
    
    if not value:
        return None
        
    try:
        # Handle times like "345" -> "3:45"
        if len(value) == 3 and ':' not in value:
            value = f"{value[0]}:{value[1:]}"
        elif len(value) == 4 and ':' not in value:
            value = f"{value[:2]}:{value[2:]}"
        
        # Ensure proper AM/PM format
        if value.endswith('A') or value.endswith('P'):
            value = value + 'M'
            
        # Add AM/PM if not present
        if not any(x in value for x in ['AM', 'PM']):
            hour = int(value.split(':')[0])
            value += 'AM' if hour < 12 else 'PM'
            
        # Parse and standardize time format
        time_obj = datetime.strptime(value, '%I:%M%p')
        return time_obj.strftime('%I:%M %p')
    except (ValueError, IndexError) as e:
        logger.warning(f"Could not parse time value: {value} - {str(e)}")
        return None

def clean_station_name(value):
    """Clean and standardize station names."""
    if pd.isna(value):
        return None
        
    value = str(value).strip()
    
    # Remove common suffixes and standardize names
    value = re.sub(r'\s+', ' ', value)
    value = value.replace(' Station', '')
    value = value.replace(' Caltrain', '')
    
    # Skip rows that don't look like station names
    if len(value) < 2 or re.match(r'^[\d:]+$', value):
        return None
        
    return value.title()

def process_table(df):
    """Process a single table and convert it to the required format."""
    processed_rows = []
    
    # Find the header row with train numbers
    header_row = None
    for idx in range(min(5, len(df))):  # Check first 5 rows
        if df.iloc[idx].astype(str).str.contains(r'^\d+$').any():
            header_row = idx
            break
    
    if header_row is None:
        logger.warning("Could not find header row with train numbers")
        return pd.DataFrame()
    
    # Get station names from the first column, starting after header row
    stations = df.iloc[header_row + 1:, 0].apply(clean_station_name)
    stations = stations[stations.notna()]
    
    # Process each column (train)
    for col in df.columns[1:]:  # Skip first column (station names)
        train_num = clean_train_number(df.iloc[header_row, col])
        if train_num:
            # Process each station for this train
            for idx, station in stations.items():
                time = clean_time(df.iloc[idx, col])
                if time:
                    processed_rows.append({
                        'train_number': train_num,
                        'station': station,
                        'time': time
                    })
    
    result_df = pd.DataFrame(processed_rows)
    if not result_df.empty:
        # Sort by train number and time
        result_df['time_obj'] = pd.to_datetime(result_df['time'], format='%I:%M %p').dt.time
        result_df = result_df.sort_values(['train_number', 'time_obj'])
        result_df = result_df.drop('time_obj', axis=1)
    
    return result_df

def validate_schedule_data(df):
    """Validate the processed schedule data."""
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Sort by train number and time
    df['time_obj'] = pd.to_datetime(df['time'], format='%I:%M %p').dt.time
    df = df.sort_values(['train_number', 'time_obj'])
    df = df.drop('time_obj', axis=1)
    
    # Validate that each train has a reasonable number of stops
    train_stops = df.groupby('train_number').size()
    suspicious_trains = train_stops[train_stops < 2]
    if not suspicious_trains.empty:
        logger.warning(f"Trains with suspiciously few stops: {suspicious_trains.index.tolist()}")
    
    return df

def main():
    # Constants
    PDF_URL = "https://www.caltrain.com/media/34716"
    PDF_PATH = Path("caltrain_schedule.pdf")
    CSV_PATH = Path("caltrain_schedule.csv")
    
    # Create workspace directory if it doesn't exist
    PDF_PATH.parent.mkdir(exist_ok=True)
    
    # Download PDF
    if not download_pdf(PDF_URL, PDF_PATH):
        logger.error("Failed to download PDF. Exiting.")
        return
    
    # Extract tables
    tables = extract_tables(PDF_PATH)
    if tables is None:
        logger.error("Failed to extract tables. Exiting.")
        return
    
    logger.info(f"Found {len(tables)} tables in the PDF")
    
    # Process each table and combine results
    processed_tables = []
    for i, table in enumerate(tables):
        logger.info(f"Processing table {i} with shape {table.shape}")
        try:
            processed_df = process_table(table)
            if not processed_df.empty:
                processed_tables.append(processed_df)
                logger.info(f"Successfully processed table {i}: found {len(processed_df)} entries")
            else:
                logger.warning(f"Table {i} yielded no valid entries")
        except Exception as e:
            logger.error(f"Error processing table {i}: {e}")
            continue
    
    if not processed_tables:
        logger.error("No valid schedule data was extracted. Exiting.")
        return
        
    # Combine all processed tables
    combined_df = pd.concat(processed_tables, ignore_index=True)
    
    # Validate and clean the final dataset
    final_df = validate_schedule_data(combined_df)
    
    # Remove any duplicate entries
    final_df = final_df.drop_duplicates()
    
    # Sort by train number and time
    final_df['time_obj'] = pd.to_datetime(final_df['time'], format='%I:%M %p').dt.time
    final_df = final_df.sort_values(['train_number', 'time_obj'])
    final_df = final_df.drop('time_obj', axis=1)
    
    # Save to CSV
    final_df.to_csv(CSV_PATH, index=False)
    
    # Log statistics about the processed data
    logger.info("\nProcessing Summary:")
    logger.info(f"Total schedule entries: {len(final_df)}")
    logger.info(f"Number of unique trains: {final_df['train_number'].nunique()}")
    logger.info(f"Number of unique stations: {final_df['station'].nunique()}")
    logger.info(f"Data saved to: {CSV_PATH}")
    
    # Sample of the data
    logger.info("\nSample of processed data:")
    logger.info(final_df.head().to_string())
    
    return final_df

if __name__ == "__main__":
    main()