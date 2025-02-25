#!/usr/bin/env python3

import os
import requests
import PyPDF2
import camelot
import pandas as pd
from pathlib import Path

def download_pdf(url, output_path):
    """Download PDF file from URL and save it to the specified path."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    return output_path

def split_pdf_by_direction(pdf_path):
    """
    Read the PDF and identify pages for northbound and southbound schedules.
    Returns a tuple of (northbound_pages, southbound_pages).
    """
    reader = PyPDF2.PdfReader(pdf_path)
    northbound_pages = []
    southbound_pages = []
    
    # Iterate through pages to identify direction based on content
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text().lower()
        
        if 'northbound' in text:
            northbound_pages.append(page_num + 1)  # camelot uses 1-based page numbers
        elif 'southbound' in text:
            southbound_pages.append(page_num + 1)
    
    return northbound_pages, southbound_pages

def extract_schedule_tables(pdf_path, pages, direction):
    """
    Extract schedule tables from specified pages using Camelot.
    Returns a list of pandas DataFrames.
    """
    all_tables = []
    
    for page in pages:
        # Extract tables from the page using Camelot
        # Use lattice mode as the schedule appears to be in a well-defined grid
        tables = camelot.read_pdf(pdf_path, pages=str(page), flavor='lattice')
        
        for table in tables:
            # Convert to pandas DataFrame
            df = table.df
            
            # Skip if table is empty or doesn't look like a schedule
            if df.empty or len(df.columns) < 2:
                continue
            
            # Add direction column
            df['direction'] = direction
            all_tables.append(df)
    
    return all_tables

def clean_time(time_str):
    """Clean and standardize time strings."""
    if pd.isna(time_str) or time_str.strip() == '':
        return None
    
    # Remove any whitespace and lowercase
    time_str = time_str.strip().lower()
    
    # Remove any 'a' or 'p' without 'm'
    time_str = time_str.replace('a', 'am').replace('p', 'pm')
    
    # Handle special cases
    if time_str in ['-', '—', '–']:
        return None
    
    try:
        # Convert to standard time format
        return pd.to_datetime(time_str).strftime('%I:%M %p')
    except:
        return None

def clean_station_name(station):
    """Clean and standardize station names."""
    if pd.isna(station):
        return None
    
    station = station.strip()
    
    # Remove common suffixes/prefixes
    station = station.replace('Station', '').replace('Transit Center', 'TC')
    
    # Standardize common station names
    replacements = {
        'San Francisco': 'SF',
        'South San Francisco': 'South SF',
        '22nd Street': '22nd St',
        '4th & King': '4th & King SF',
    }
    
    for old, new in replacements.items():
        if old in station:
            station = station.replace(old, new)
    
    return station.strip()

def extract_train_number(df):
    """Extract train numbers from the DataFrame header."""
    # Usually train numbers are in the first row
    train_numbers = []
    for col in df.columns[1:]:  # Skip first column (stations)
        try:
            # Extract numeric part
            num = ''.join(filter(str.isdigit, df.iloc[0][col]))
            train_numbers.append(int(num) if num else None)
        except:
            train_numbers.append(None)
    return train_numbers

def transform_schedule_data(tables):
    """
    Transform and clean the schedule data into the required format.
    Returns a DataFrame with columns [direction, train_number, station, time]
    """
    cleaned_data = []
    
    for df in tables:
        # Get direction
        direction = df['direction'].iloc[0]
        
        # Extract train numbers from the first row
        train_numbers = extract_train_number(df)
        
        # Process each row (station) and column (time)
        for idx, row in df.iloc[1:].iterrows():  # Skip header row
            station = clean_station_name(row.iloc[0])  # First column is station name
            
            if not station:  # Skip rows without valid station names
                continue
            
            # Process each time column
            for col_idx, time in enumerate(row.iloc[1:]):  # Skip station column
                if col_idx >= len(train_numbers):
                    continue
                    
                train_number = train_numbers[col_idx]
                cleaned_time = clean_time(time)
                
                if train_number and cleaned_time:
                    cleaned_data.append({
                        'direction': direction,
                        'train_number': train_number,
                        'station': station,
                        'time': cleaned_time
                    })
    
    # Convert to DataFrame
    result_df = pd.DataFrame(cleaned_data)
    
    # Sort by direction, train_number, and time
    result_df = result_df.sort_values(['direction', 'train_number', 'time'])
    
    return result_df

def validate_schedule_data(df):
    """
    Perform sanity checks on the cleaned schedule data.
    Returns True if data passes all checks, raises Exception otherwise.
    """
    # Check if we have all required columns
    required_columns = ['direction', 'train_number', 'station', 'time']
    if not all(col in df.columns for col in required_columns):
        raise Exception("Missing required columns in the cleaned data")
    
    # Check for null values
    if df[required_columns].isnull().any().any():
        raise Exception("Found null values in required columns")
    
    # Check direction values
    valid_directions = {'Northbound', 'Southbound'}
    if not set(df['direction'].unique()).issubset(valid_directions):
        raise Exception("Invalid direction values found")
    
    # Check train numbers
    if not df['train_number'].apply(lambda x: isinstance(x, (int, float))).all():
        raise Exception("Invalid train numbers found")
    
    # Check time format
    time_pattern = r'\d{1,2}:\d{2} [AP]M'
    if not df['time'].str.match(time_pattern).all():
        raise Exception("Invalid time format found")
    
    # Check that each train's times are sequential within each direction
    for direction in df['direction'].unique():
        for train in df[df['direction'] == direction]['train_number'].unique():
            train_times = df[
                (df['direction'] == direction) & 
                (df['train_number'] == train)
            ]['time']
            
            if not (pd.to_datetime(train_times).is_monotonic_increasing):
                raise Exception(f"Non-sequential times found for {direction} train {train}")
    
    return True

def main():
    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Download the PDF
    pdf_url = 'https://www.caltrain.com/media/34716'
    pdf_path = data_dir / 'caltrain_schedule.pdf'
    
    print(f"Downloading PDF from {pdf_url}...")
    download_pdf(pdf_url, pdf_path)
    print(f"PDF downloaded to {pdf_path}")
    
    # Split PDF by direction
    print("Analyzing PDF to identify northbound and southbound schedules...")
    northbound_pages, southbound_pages = split_pdf_by_direction(pdf_path)
    print(f"Found northbound pages: {northbound_pages}")
    print(f"Found southbound pages: {southbound_pages}")
    
    # Extract tables for both directions
    print("Extracting schedule tables...")
    northbound_tables = extract_schedule_tables(pdf_path, northbound_pages, "Northbound")
    southbound_tables = extract_schedule_tables(pdf_path, southbound_pages, "Southbound")
    
    print(f"Extracted {len(northbound_tables)} northbound tables")
    print(f"Extracted {len(southbound_tables)} southbound tables")
    
    # Combine all tables
    all_tables = northbound_tables + southbound_tables
    
    # Basic validation of extracted data
    if not all_tables:
        raise Exception("No tables were successfully extracted from the PDF")
    
    print("Transforming and cleaning schedule data...")
    cleaned_df = transform_schedule_data(all_tables)
    
    print("Validating cleaned data...")
    validate_schedule_data(cleaned_df)
    
    # Save to CSV
    csv_path = data_dir / 'caltrain_schedule.csv'
    cleaned_df.to_csv(csv_path, index=False)
    print(f"Schedule data saved to {csv_path}")
    
    # Print some statistics
    print("\nSchedule Statistics:")
    print(f"Total number of stops: {len(cleaned_df)}")
    print(f"Number of trains: {cleaned_df['train_number'].nunique()}")
    print(f"Number of stations: {cleaned_df['station'].nunique()}")
    print("\nSample of the cleaned data:")
    print(cleaned_df.head())

if __name__ == '__main__':
    main()