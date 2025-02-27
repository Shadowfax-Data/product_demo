#!/usr/bin/env python3
import argparse
import csv
import datetime
import json
import requests
from typing import List, Dict
from dateutil.relativedelta import relativedelta
from dateutil import parser

def format_date(date: datetime.date) -> str:
    """Format date as MM/DD/YYYY for the API."""
    return date.strftime("%m/%d/%Y")

def get_month_ranges(start_date: datetime.date, end_date: datetime.date) -> List[tuple]:
    """Generate list of month start/end date pairs between start and end dates."""
    ranges = []
    current = start_date.replace(day=1)
    
    while current <= end_date:
        month_end = min(
            (current + relativedelta(months=1, days=-1)),
            end_date
        )
        ranges.append((current, month_end))
        current = current + relativedelta(months=1, days=0)
    
    return ranges

def fetch_egg_data(report_id: int, start_date: str, end_date: str) -> List[Dict]:
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
    
    start = parser.parse(start_date).date()
    end = parser.parse(end_date).date()
    
    all_results = []
    date_ranges = get_month_ranges(start, end)
    
    for range_start, range_end in date_ranges:
        url = f'https://mymarketnews.ams.usda.gov/public_data/ajax-search-data-by-report/{report_id}'
        params = {
            'q': f'report_begin_date={format_date(range_start)}:{format_date(range_end)}'
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('results'):
            print(f"Warning: No data found for range {range_start} to {range_end}")
            continue
            
        all_results.extend(data['results'])
        print(f"Fetched {len(data['results'])} records for {range_start} to {range_end}")
    
    return all_results

def save_to_csv(data: List[Dict], output_file: str):
    """Save the egg inventory data to a CSV file."""
    if not data:
        print("No data to save")
        return
    
    fieldnames = [
        'report_date', 'region', 'class', 'type', 'volume', 
        'pct_chg_last_week', 'package', 'commodity', 'final_ind'
    ]
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            writer.writerow({
                'report_date': row['report_date'],
                'region': row['region'],
                'class': row['class'] or row['type'],
                'type': row['type'],
                'volume': row['volume'],
                'pct_chg_last_week': row['pct_chg_last_week'],
                'package': row['package'],
                'commodity': row['commodity'],
                'final_ind': row['final_ind']
            })

def main():
    parser = argparse.ArgumentParser(description='Fetch USDA egg inventory data')
    parser.add_argument('--report-id', type=int, default=1427,
                      help='Report ID (default: 1427 for National Weekly Shell Egg Inventory)')
    parser.add_argument('--start-date', default='1/1/2024',
                      help='Start date in MM/DD/YYYY format (default: 1/1/2024)')
    parser.add_argument('--end-date', default='2/28/2025',
                      help='End date in MM/DD/YYYY format (default: 2/28/2025)')
    parser.add_argument('--output', required=True,
                      help='Output CSV file path')
    
    args = parser.parse_args()
    
    try:
        data = fetch_egg_data(args.report_id, args.start_date, args.end_date)
        save_to_csv(data, args.output)
        print(f"Successfully saved {len(data)} records to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()