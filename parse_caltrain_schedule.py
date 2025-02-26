import requests
import tabula
import pandas as pd
import numpy as np
from pathlib import Path
import re

def download_pdf(url, output_path):
    response = requests.get(url)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    return output_path

def extract_tables(pdf_path):
    """Extract tables from PDF using multiple methods and pages."""
    all_tables = []
    
    # Try different extraction methods
    methods = [
        {'pages': '1', 'area': [50, 50, 750, 550]},
        {'pages': '2', 'area': [50, 50, 750, 550]},
        {'pages': '3', 'area': [50, 50, 750, 550]},
        {'pages': '4', 'area': [50, 50, 750, 550]},
        {'pages': '1-2', 'area': None},
        {'pages': '3-4', 'area': None},
    ]
    
    for method in methods:
        try:
            # Extract with current method
            kwargs = {
                'pages': method['pages'],
                'multiple_tables': True,
                'pandas_options': {'header': None},
                'java_options': ["-Dfile.encoding=UTF8"],
                'silent': True,
                'guess': False
            }
            
            if method['area']:
                kwargs['area'] = method['area']
            
            # Try stream mode
            tables = tabula.read_pdf(pdf_path, stream=True, **kwargs)
            all_tables.extend(tables)
            
            # Try lattice mode
            tables = tabula.read_pdf(pdf_path, lattice=True, **kwargs)
            all_tables.extend(tables)
            
        except Exception as e:
            print(f"Warning: Extraction failed for pages {method['pages']}: {e}")
            continue
    
    # Clean and filter tables
    cleaned_tables = []
    for table in all_tables:
        if table is None or table.empty:
            continue
        
        # Basic cleaning
        table = table.dropna(how='all', axis=0).dropna(how='all', axis=1)
        
        if table.shape[0] > 5 and table.shape[1] > 5:
            # Convert to string and clean
            table = table.astype(str)
            table = table.replace({
                'nan': '', 'None': '', 'NaN': '', 'NaT': '',
                'null': '', 'NULL': '', 'Null': '', '-': '',
                '—': '', '–': '', '−': ''  # Handle different types of dashes
            })
            
            # Remove rows/cols that are all empty after cleaning
            table = table.loc[~(table == '').all(axis=1)]
            table = table.loc[:, ~(table == '').all(axis=0)]
            
            if table.shape[0] > 5 and table.shape[1] > 5:
                # Check if this table looks like a schedule
                time_pattern = r'\d{1,2}:\d{2}'
                station_pattern = r'(San Francisco|San Jose|Millbrae|Palo Alto|Mountain View|Sunnyvale)'
                
                # Look for times in any column except the first
                has_times = table.iloc[:, 1:].apply(lambda x: x.str.contains(time_pattern, regex=True, na=False)).any().any()
                # Look for station names in the first column
                has_stations = table.iloc[:, 0].str.contains(station_pattern, regex=True, case=False, na=False).any()
                
                if has_times and has_stations:
                    # Clean up the table format
                    table = table.replace(r'^\s*$', '', regex=True)
                    cleaned_tables.append(table)
    
    # Remove duplicates
    unique_tables = []
    seen = set()
    
    for table in cleaned_tables:
        # Create a signature for the table
        signature = (
            table.shape[0],
            table.shape[1],
            table.iloc[0:3, 0:3].to_string(),  # Use first few cells as signature
            table.iloc[-3:, 0:3].to_string()   # Also use last few cells
        )
        
        if signature not in seen:
            seen.add(signature)
            unique_tables.append(table)
    
    print(f"Found {len(unique_tables)} potential schedule tables")
    return unique_tables

def analyze_table_content(table):
    """Analyze table content to determine if it's a schedule table and its direction."""
    # Convert to string for analysis
    table_str = table.astype(str)
    
    # Define station patterns for each direction
    station_patterns = {
        'northbound': [
            'San Jose', 'Tamien', 'Capitol', 'Blossom Hill', 'Morgan Hill', 'Gilroy',
            'Lawrence', 'Santa Clara', 'College Park', 'San Antonio', 'Mountain View',
            'Sunnyvale', 'Redwood City', 'Menlo Park'
        ],
        'southbound': [
            'San Francisco', '4th & King', '22nd Street', 'Bayshore', 'South SF',
            'San Bruno', 'Millbrae', 'Broadway', 'Burlingame', 'San Mateo',
            'Hillsdale', 'Belmont', 'San Carlos'
        ]
    }
    
    # Find rows with station names and their indices
    station_info = []  # [(row_index, station_name, direction)]
    
    for idx, row in enumerate(table_str.iloc[:, 0]):
        row_lower = row.lower()
        for direction, patterns in station_patterns.items():
            for station in patterns:
                if station.lower() in row_lower:
                    station_info.append((idx, station, direction))
                    break
    
    if not station_info:
        return False, None
    
    # Sort station info by row index to maintain order
    station_info.sort(key=lambda x: x[0])
    
    # Count stations for each direction in the first few and last few stations
    first_stations = station_info[:3]
    last_stations = station_info[-3:]
    
    direction_scores = {'northbound': 0, 'southbound': 0}
    
    # Check first stations (weighted more heavily)
    for _, _, direction in first_stations:
        direction_scores[direction] += 2
    
    # Check last stations
    for _, _, direction in last_stations:
        direction_scores[direction] += 1
    
    # Additional check: look for key terminal stations
    terminals = {
        'northbound': ['San Francisco', '4th & King'],
        'southbound': ['Gilroy', 'San Jose Diridon']
    }
    
    first_station = table_str.iloc[station_info[0][0], 0].lower()
    last_station = table_str.iloc[station_info[-1][0], 0].lower()
    
    # If a terminal station is at the start or end, it strongly indicates direction
    for direction, terms in terminals.items():
        for term in terms:
            if term.lower() in first_station:
                direction_scores[direction] += 3
            if term.lower() in last_station:
                direction_scores[direction] += 3
    
    # Determine direction based on scores
    if direction_scores['northbound'] > direction_scores['southbound']:
        return True, 'northbound'
    elif direction_scores['southbound'] > direction_scores['northbound']:
        return True, 'southbound'
    
    # If still unclear, check the overall station count
    direction_counts = {'northbound': 0, 'southbound': 0}
    for _, _, direction in station_info:
        direction_counts[direction] += 1
    
    if direction_counts['northbound'] > direction_counts['southbound']:
        return True, 'northbound'
    elif direction_counts['southbound'] > direction_counts['northbound']:
        return True, 'southbound'
    
    return False, None

def is_main_schedule_table(table):
    """Check if the table is a main schedule table and determine its direction."""
    if table.shape[0] < 10 or table.shape[1] < 5:
        return False, None
    
    is_schedule, direction = analyze_table_content(table)
    return is_schedule, direction

def clean_station_name(station):
    """Clean and standardize station names."""
    station = str(station).strip()
    
    # Skip if station name is too short or contains unwanted patterns
    if len(station) < 3 or any(x in station.lower() for x in 
                              ['train', 'note', 'time', 'stop', 'zone']):
        return None
    
    # Common station name patterns and their full names
    station_patterns = {
        r'S\.?F\.?\s*4th': 'San Francisco 4th & King',
        r'4th\s*&\s*King': 'San Francisco 4th & King',
        r'22nd\s*St': '22nd Street',
        r'So\.?\s*San\s*Francisco': 'South San Francisco',
        r'S\.?\s*San\s*Francisco': 'South San Francisco',
        r'South\s*SF': 'South San Francisco',
        r'Mt\.?\s*View': 'Mountain View',
        r'Mtn\.?\s*View': 'Mountain View',
        r'ntain\s*View': 'Mountain View',
        r'San\s*Jose\s*Dir': 'San Jose Diridon',
        r'ose\s*Dir': 'San Jose Diridon',
        r'ose\s*Diridon': 'San Jose Diridon',
        r'an\s*Antonio': 'San Antonio',
        r'anta\s*Clara': 'Santa Clara',
        r'dwood\s*City': 'Redwood City',
        r'n\s*Francisco': 'San Francisco',
        r'nia\s*Avenue': 'California Avenue',
        r'yward\s*Park': 'Hayward Park',
        r'lossom\s*Hill': 'Blossom Hill',
        r'ollege\s*Park': 'College Park',
        r'organ\s*Hill': 'Morgan Hill',
        r'urlingame': 'Burlingame',
        r'College\s*Park\s*[–—-]+': 'College Park',
        r'ZONE\s*\d+(?:\s*ZONE\s*\d+)*': None,  # Skip zone information
        r'[–—-]+': None,  # Skip rows with just dashes
        r'^\s*\d+\s*$': None  # Skip rows with just numbers
    }
    
    # Try to match and replace truncated or abbreviated names
    station_lower = station.lower()
    for pattern, full_name in station_patterns.items():
        if re.search(pattern, station, re.IGNORECASE):
            return full_name
    
    # Remove common suffixes and standardize names
    replacements = {
        'Station': '',
        'Transit Center': 'TC',
        'Caltrain': '',
        '(Tamien)': 'Tamien',
    }
    
    for old, new in replacements.items():
        station = station.replace(old, new).strip()
    
    # Remove any parentheses and their contents
    station = re.sub(r'\([^)]*\)', '', station).strip()
    
    # Remove any sequences of dashes or similar characters
    station = re.sub(r'[–—-]+', '', station).strip()
    
    # Remove multiple spaces
    station = ' '.join(station.split())
    
    # Final check for minimum length and no unwanted characters
    if len(station) >= 3 and not re.search(r'[–—-]', station):
        return station
    return None

def validate_time(time_str):
    """Validate and standardize time format."""
    if pd.isna(time_str) or time_str in ['–', '-', '', '—']:
        return None
    
    time_str = str(time_str).strip().upper()
    
    # Handle special cases
    if time_str.startswith('D'):  # Day after
        time_str = time_str[1:]
    
    # Try to extract time using regex
    time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
    if not time_match:
        return None
    
    try:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        
        # Handle special cases for times after midnight
        if hours == 24:
            hours = 0
        elif hours > 24:
            return None
        
        # Validate minutes
        if not (0 <= minutes <= 59):
            return None
        
        # Return standardized time format
        return f"{hours:02d}:{minutes:02d}"
    except ValueError:
        return None

def clean_train_number(train_num):
    """Clean and validate train number."""
    train_num = str(train_num).strip()
    
    # Try to extract a number from the string
    match = re.search(r'(\d+)', train_num)
    if not match:
        return None
        
    number = match.group(1)
    
    # Validate the number is in a reasonable range (1-999)
    try:
        num_val = int(number)
        if 1 <= num_val <= 999:
            return str(num_val)
    except ValueError:
        pass
    
    return None

def process_schedule_table(table, direction):
    """Process a schedule table and extract train times."""
    # Convert all values to string and clean up
    table = table.astype(str).replace({'nan': '', 'None': '', 'NaN': '', 'NaT': ''})
    
    # Find rows with time patterns (these are likely the data rows)
    time_pattern = r'\d{1,2}:\d{2}'
    time_rows = []
    for idx, row in table.iterrows():
        if row.astype(str).str.contains(time_pattern, regex=True).any():
            time_rows.append(idx)
    
    if not time_rows:
        return pd.DataFrame(columns=['direction', 'train_number', 'station', 'time'])
    
    # Find train numbers (they should be in the header, above the time rows)
    first_time_row = min(time_rows)
    train_cols = {}  # {column_index: train_number}
    
    for col in range(1, table.shape[1]):
        # Look for train numbers in header rows
        header_values = table.iloc[0:first_time_row, col].astype(str)
        for val in header_values:
            # Try to extract a train number
            if val.strip().isdigit():
                train_cols[col] = val.strip()
                break
            # Try to extract number from text
            match = re.search(r'\d+', val)
            if match:
                train_cols[col] = match.group()
                break
    
    if not train_cols:
        return pd.DataFrame(columns=['direction', 'train_number', 'station', 'time'])
    
    records = []
    current_station = None
    
    # Process each row
    for row_idx in range(table.shape[0]):
        # Check if this is a station name in column 0
        station = table.iloc[row_idx, 0].strip()
        if station and not re.search(time_pattern, station):
            clean_station = clean_station_name(station)
            if clean_station:
                current_station = clean_station
        
        # Skip if we don't have a valid station
        if not current_station:
            continue
        
        # Process each train column
        for col_idx, train_num in train_cols.items():
            if col_idx >= table.shape[1]:
                continue
                
            time_str = table.iloc[row_idx, col_idx].strip()
            valid_time = validate_time(time_str)
            
            if valid_time:
                records.append({
                    'direction': direction,
                    'train_number': train_num,
                    'station': current_station,
                    'time': valid_time
                })
    
    if not records:
        return pd.DataFrame(columns=['direction', 'train_number', 'station', 'time'])
    
    # Create DataFrame and sort by train number and time
    df = pd.DataFrame(records)
    df['time_sort'] = pd.to_datetime(df['time'], format='%H:%M')
    df = df.sort_values(['train_number', 'time_sort'])
    df = df.drop('time_sort', axis=1)
    
    # Remove any duplicate station/train/time combinations
    df = df.drop_duplicates(['train_number', 'station', 'time'])
    
    return df

def identify_direction(table):
    """Identify if a table is northbound or southbound based on its content."""
    first_col = table.iloc[:, 0].astype(str)
    
    # Look for direction indicators in the first column
    sf_indicators = ['San Francisco', 'SF', '4th & King']
    sj_indicators = ['San Jose', 'Gilroy', 'Tamien']
    
    # Check first few rows and last few rows
    sample_rows = pd.concat([first_col.head(5), first_col.tail(5)])
    
    # If San Francisco appears first, it's southbound (starting from SF)
    # If San Jose/Gilroy appears first, it's northbound (heading to SF)
    sf_first = False
    sj_first = False
    
    for val in sample_rows:
        if any(ind in str(val) for ind in sf_indicators):
            sf_first = True
            break
        if any(ind in str(val) for ind in sj_indicators):
            sj_first = True
            break
    
    if sf_first:
        return 'southbound'
    elif sj_first:
        return 'northbound'
    return None

def validate_schedule_data(df):
    """Validate and clean the schedule data."""
    # Remove rows with missing values
    df = df.dropna()
    
    # Remove duplicates
    df = df.drop_duplicates(['direction', 'train_number', 'station', 'time'])
    
    # Sort by direction, train number, and time
    df['time_sort'] = pd.to_datetime(df['time'], format='%H:%M')
    df = df.sort_values(['direction', 'train_number', 'time_sort'])
    
    # Validate each train has a reasonable number of stops
    train_stops = df.groupby(['direction', 'train_number']).size()
    valid_trains = train_stops[train_stops >= 5].index
    df = df[df.set_index(['direction', 'train_number']).index.isin(valid_trains)]
    
    # Validate station sequence (times should be increasing)
    def validate_station_sequence(group):
        times = group['time_sort'].tolist()
        return all(times[i] <= times[i+1] for i in range(len(times)-1))
    
    valid_sequences = df.groupby(['direction', 'train_number']).apply(validate_station_sequence)
    valid_trains = valid_sequences[valid_sequences].index
    df = df[df.set_index(['direction', 'train_number']).index.isin(valid_trains)]
    
    # Drop the temporary sorting column
    df = df.drop('time_sort', axis=1)
    
    return df

def main():
    # URL of the Caltrain schedule PDF
    pdf_url = "https://www.caltrain.com/media/34716"
    pdf_path = "caltrain_schedule.pdf"
    
    try:
        # Download the PDF
        print("Downloading PDF...")
        download_pdf(pdf_url, pdf_path)
        
        # Extract tables from PDF
        print("Extracting tables from PDF...")
        tables = extract_tables(pdf_path)
        
        # Process tables
        all_schedules = []
        
        print("Processing schedule tables...")
        for table in tables:
            is_schedule, direction = is_main_schedule_table(table)
            if is_schedule and direction:
                print(f"Processing {direction} schedule table...")
                print(f"Table shape: {table.shape}")
                schedule_df = process_schedule_table(table, direction)
                if not schedule_df.empty:
                    all_schedules.append(schedule_df)
                    print(f"Extracted {len(schedule_df)} records")
        
        if not all_schedules:
            raise ValueError("No valid schedule data could be extracted from the PDF")
        
        # Combine all schedules
        print("\nCombining and validating schedules...")
        final_schedule = pd.concat(all_schedules, ignore_index=True)
        final_schedule = validate_schedule_data(final_schedule)
        
        if final_schedule.empty:
            raise ValueError("No valid schedule data after validation")
        
        # Print validation results
        print("\nValidation Results:")
        print(f"Total stations: {final_schedule['station'].nunique()}")
        print("Stations found:", sorted(final_schedule['station'].unique()))
        print(f"\nTotal trains: {final_schedule['train_number'].nunique()}")
        print("Train numbers:", sorted(final_schedule['train_number'].unique()))
        print(f"\nRecords by direction:")
        print(final_schedule['direction'].value_counts())
        
        # Save to CSV
        final_schedule.to_csv('caltrain_schedule.csv', index=False)
        print("\nSchedule saved to caltrain_schedule.csv")
        
        # Print sample of the data
        print("\nSample of processed data:")
        print(final_schedule.head(10))
        print(f"\nTotal records: {len(final_schedule)}")
        
        # Print some statistics
        print("\nStatistics by direction:")
        for direction in final_schedule['direction'].unique():
            dir_data = final_schedule[final_schedule['direction'] == direction]
            print(f"\n{direction.title()} trains:")
            print(f"Number of trains: {dir_data['train_number'].nunique()}")
            print(f"Average stops per train: {len(dir_data) / dir_data['train_number'].nunique():.1f}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise
    finally:
        # Clean up downloaded PDF
        if Path(pdf_path).exists():
            Path(pdf_path).unlink()

if __name__ == "__main__":
    main()