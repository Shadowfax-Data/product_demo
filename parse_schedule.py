import requests
import tabula
import pandas as pd
from pathlib import Path
import tempfile

def download_pdf(url, output_path):
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        f.write(response.content)
    return output_path

def parse_schedule_tables(pdf_path):
    # Extract all tables from the PDF
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
    
    # Initialize list to store processed data
    all_data = []
    
    for table in tables:
        if table.empty:
            continue
        
        # Reset the index to handle unnamed columns
        table = table.reset_index(drop=True)
        
        # The first column typically contains station names
        station_col = table.columns[0]
        
        # Get column names that contain train numbers (typically numeric columns)
        train_columns = [col for col in table.columns if str(col).strip().isdigit()]
        
        if len(train_columns) == 0:
            continue
        
        # Process each train column
        for train_num in train_columns:
            # Extract station and time data
            station_times = table[[station_col, train_num]].copy()
            
            # Remove rows where both station and time are NaN
            station_times = station_times.dropna(how='all')
            
            # Skip if no data
            if station_times.empty:
                continue
            
            # Rename columns for clarity
            station_times.columns = ['station', 'time']
            
            # Add train number
            station_times['train_number'] = train_num
            
            # Reorder columns to match desired output
            station_times = station_times[['train_number', 'station', 'time']]
            
            all_data.append(station_times)
    
    # Combine all processed data
    if not all_data:
        raise ValueError("No valid schedule data found in PDF")
        
    combined_data = pd.concat(all_data, ignore_index=True)
    return combined_data

def clean_data(df):
    # Remove any rows where station or time is missing
    df = df.dropna(subset=['station', 'time'])
    
    # Clean station names
    df['station'] = df['station'].astype(str).str.strip()
    
    # Remove any rows with empty strings or non-informative content
    df = df[
        (df['station'] != '') & 
        (~df['station'].str.lower().isin(['station', 'stop', 'stations']))
    ]
    
    # Convert train_number to integer
    df['train_number'] = df['train_number'].astype(int)
    
    # Clean time strings
    df['time'] = df['time'].astype(str).str.strip()
    
    # Sort by train number and keep only valid rows
    df = df.sort_values('train_number').reset_index(drop=True)
    
    return df

def main():
    # URL of the Caltrain schedule PDF
    pdf_url = "https://www.caltrain.com/media/34716"
    
    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
        pdf_path = temp_pdf.name
        
        try:
            # Download the PDF
            print("Downloading PDF...")
            download_pdf(pdf_url, pdf_path)
            
            # Parse the tables
            print("Parsing schedule tables...")
            schedule_data = parse_schedule_tables(pdf_path)
            
            # Clean the data
            print("Cleaning data...")
            cleaned_data = clean_data(schedule_data)
            
            # Save to CSV
            output_path = Path('caltrain_schedule.csv')
            cleaned_data.to_csv(output_path, index=False)
            print(f"Schedule data saved to {output_path}")
            
        finally:
            # Clean up the temporary PDF file
            Path(pdf_path).unlink()

if __name__ == "__main__":
    main()