import requests
import tabula
import pandas as pd
import re
from pathlib import Path
from datetime import datetime

def download_pdf(url, output_path):
    """Download PDF file from URL."""
    response = requests.get(url)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    return output_path

def extract_schedule_tables(pdf_path):
    """Extract tables from PDF using tabula."""
    tables = tabula.read_pdf(
        pdf_path,
        pages='all',
        multiple_tables=True,
        lattice=True
    )
    return tables

def is_valid_time(time_str):
    """Validate time string format (HH:MM or H:MM)."""
    if not isinstance(time_str, str):
        return False
    time_pattern = re.compile(r'^([0-9]|0[0-9]|1[0-2]):([0-5][0-9])$')
    return bool(time_pattern.match(time_str))

def is_train_number(value):
    """Check if value is a valid train number."""
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str) and value.strip().isdigit():
        return True
    return False

def clean_time(time_str):
    """Clean and standardize time format."""
    if not isinstance(time_str, str):
        return None
    time_str = time_str.strip()
    if not time_str:
        return None
    
    # Remove any extra whitespace or characters
    time_str = re.sub(r'[^0-9:]', '', time_str)
    
    # Validate the cleaned time
    if is_valid_time(time_str):
        return time_str
    return None

def process_schedule_table(table):
    """Process a single schedule table and extract train numbers, stations, and times."""
    if table.empty:
        return pd.DataFrame()
    
    # First row typically contains train numbers
    train_numbers = []
    for col in table.columns:
        if is_train_number(col):
            train_numbers.append(int(float(col)))
    
    # Process each row (station) and its times
    schedule_data = []
    for _, row in table.iterrows():
        station = row.iloc[0]  # First column is usually the station name
        if not isinstance(station, str) or not station.strip():
            continue
            
        station = station.strip()
        for train_num, time in zip(train_numbers, row[1:len(train_numbers)+1]):
            clean_time_val = clean_time(str(time))
            if clean_time_val:
                schedule_data.append({
                    'train_number': train_num,
                    'station': station,
                    'time': clean_time_val
                })
    
    return pd.DataFrame(schedule_data)

def combine_schedule_tables(tables):
    """Combine all processed schedule tables into a single DataFrame."""
    all_schedules = []
    for table in tables:
        processed_table = process_schedule_table(table)
        if not processed_table.empty:
            all_schedules.append(processed_table)
    
    if not all_schedules:
        return pd.DataFrame()
    
    combined_schedule = pd.concat(all_schedules, ignore_index=True)
    return combined_schedule.sort_values(['train_number', 'time'])

def main():
    # URLs and paths
    pdf_url = "https://www.caltrain.com/media/34716"
    pdf_path = Path("caltrain_schedule.pdf")
    csv_path = Path("caltrain_schedule.csv")
    
    try:
        # Download PDF
        print("Downloading PDF...")
        download_pdf(pdf_url, pdf_path)
        print(f"PDF downloaded to {pdf_path}")
        
        # Extract tables
        print("Extracting tables from PDF...")
        tables = extract_schedule_tables(pdf_path)
        print(f"Extracted {len(tables)} tables from PDF")
        
        # Process and combine tables
        print("Processing schedule data...")
        combined_schedule = combine_schedule_tables(tables)
        
        # Validate the processed data
        if combined_schedule.empty:
            raise ValueError("No valid schedule data was extracted from the tables")
            
        print("\nProcessed data summary:")
        print(f"Total number of schedule entries: {len(combined_schedule)}")
        print(f"Number of unique trains: {combined_schedule['train_number'].nunique()}")
        print(f"Number of unique stations: {combined_schedule['station'].nunique()}")
        
        # Display sample of processed data
        print("\nSample of processed data:")
        print(combined_schedule.head())
        
        # Export to CSV
        print("\nExporting data to CSV...")
        combined_schedule.to_csv(csv_path, index=False)
        print(f"Data exported to {csv_path}")
        
        return combined_schedule
            
    except Exception as e:
        print(f"Error occurred: {e}")
        return pd.DataFrame()
    finally:
        # Clean up downloaded PDF
        if pdf_path.exists():
            pdf_path.unlink()

if __name__ == "__main__":
    main()