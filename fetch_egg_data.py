#!/usr/bin/env python3
import argparse
import csv
from datetime import datetime, timedelta
import requests
import sys

def format_date(date_obj):
    """Format date object to MM/DD/YYYY format."""
    return date_obj.strftime("%m/%d/%Y")

def get_month_range(start_date, end_date):
    """Generate list of month start/end date pairs between start and end dates."""
    current = start_date.replace(day=1)
    while current <= end_date:
        month_end = min(
            (current.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
            end_date
        )
        yield current, month_end
        current = (current.replace(day=1) + timedelta(days=32)).replace(day=1)

def fetch_egg_data(report_id, start_date, end_date):
    """Fetch egg inventory data from USDA API with pagination by month."""
    headers = {
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    all_results = []
    
    for month_start, month_end in get_month_range(start_date, end_date):
        date_range = f"{format_date(month_start)}:{format_date(month_end)}"
        url = f"https://mymarketnews.ams.usda.gov/public_data/ajax-search-data-by-report/{report_id}"
        params = {'q': f'report_begin_date={date_range}'}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching data for {date_range}: {response.status_code}", file=sys.stderr)
            continue
            
        data = response.json()
        if not data.get('results'):
            print(f"No data found for {date_range}", file=sys.stderr)
            continue
            
        all_results.extend(data['results'])
        print(f"Fetched {len(data['results'])} records for {date_range}", file=sys.stderr)
    
    return all_results

def write_csv(data, output_file):
    """Write egg inventory data to CSV file."""
    if not data:
        print("No data to write", file=sys.stderr)
        return
    
    fieldnames = [
        'report_date',
        'region',
        'egg_class',
        'volume',
        'pct_chg_last_week',
        'package'
    ]
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in data:
            # Skip records without volume data
            if record.get('volume') is None:
                continue
                
            # Combine type and class fields
            egg_class = record.get('type') if record.get('type') != 'N/A' else record.get('class')
            if not egg_class:
                continue
                
            writer.writerow({
                'report_date': record['report_date'],
                'region': record['region'],
                'egg_class': egg_class,
                'volume': record['volume'],
                'pct_chg_last_week': record['pct_chg_last_week'],
                'package': record['package']
            })

def main():
    parser = argparse.ArgumentParser(description='Fetch USDA egg inventory data')
    parser.add_argument('--report-id', type=int, default=1427,
                      help='Report ID (default: 1427 for National Weekly Shell Egg Inventory)')
    parser.add_argument('--start-date', type=str, default='1/1/2024',
                      help='Start date in MM/DD/YYYY format (default: 1/1/2024)')
    parser.add_argument('--end-date', type=str, default='2/28/2025',
                      help='End date in MM/DD/YYYY format (default: 2/28/2025)')
    parser.add_argument('--output', type=str, required=True,
                      help='Output CSV file path')
    
    args = parser.parse_args()
    
    try:
        start_date = datetime.strptime(args.start_date, "%m/%d/%Y")
        end_date = datetime.strptime(args.end_date, "%m/%d/%Y")
    except ValueError as e:
        print(f"Error parsing dates: {e}", file=sys.stderr)
        sys.exit(1)
    
    if start_date > end_date:
        print("Start date must be before end date", file=sys.stderr)
        sys.exit(1)
    
    data = fetch_egg_data(args.report_id, start_date, end_date)
    write_csv(data, args.output)
    print(f"Data written to {args.output}", file=sys.stderr)

if __name__ == '__main__':
    main()