#!/usr/bin/env python3

import argparse
import csv
import datetime
import json
import sys
from typing import Dict, List

import requests

def format_date(date_str: str) -> str:
    """Convert date string to MM/DD/YYYY format."""
    try:
        if isinstance(date_str, datetime.date):
            return date_str.strftime("%m/%d/%Y")
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%m/%d/%Y")
    except ValueError:
        try:
            date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
            return date_str
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD or MM/DD/YYYY format")

def fetch_egg_inventory_data(report_id: int, start_date: str, end_date: str) -> Dict:
    """Fetch egg inventory data from USDA API."""
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

    formatted_start = format_date(start_date)
    formatted_end = format_date(end_date)
    date_range = f"{formatted_start}:{formatted_end}"
    
    url = f'https://mymarketnews.ams.usda.gov/public_data/ajax-search-data-by-report/{report_id}'
    params = {'q': f'report_begin_date={date_range}'}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        sys.exit(1)

def parse_inventory_data(json_data: Dict) -> List[Dict]:
    """Parse JSON response into structured data."""
    parsed_data = []
    
    for item in json_data.get('results', []):
        report_date = item.get('report_date')
        
        # Extract inventory data from the report text
        report_text = item.get('report_text', '')
        
        # Find the inventory volume in the report text
        # Example format: "Shell Eggs: 1,234,567 dozen"
        import re
        inventory_match = re.search(r'Shell Eggs:\s*([\d,]+)\s*dozen', report_text)
        if inventory_match:
            inventory_volume = int(inventory_match.group(1).replace(',', ''))
            
            parsed_data.append({
                'report_date': report_date,
                'inventory_volume': inventory_volume
            })
    
    return parsed_data

def save_to_csv(data: List[Dict], output_file: str):
    """Save parsed data to CSV file."""
    if not data:
        print("No data to write to CSV", file=sys.stderr)
        sys.exit(1)

    try:
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['report_date', 'inventory_volume']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f"Data successfully written to {output_file}")
    except IOError as e:
        print(f"Error writing to CSV file: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Download USDA egg inventory data')
    parser.add_argument('--report-id', type=int, default=1427,
                      help='Report ID (default: 1427 for National Weekly Shell Egg Inventory)')
    parser.add_argument('--start-date', type=str, default='2024-01-01',
                      help='Start date in YYYY-MM-DD format (default: 2024-01-01)')
    parser.add_argument('--end-date', type=str,
                      default=datetime.date.today().strftime('%Y-%m-%d'),
                      help='End date in YYYY-MM-DD format (default: current date)')
    parser.add_argument('--output', type=str, required=True,
                      help='Output CSV file path')

    args = parser.parse_args()

    # Fetch data
    json_data = fetch_egg_inventory_data(args.report_id, args.start_date, args.end_date)
    
    # Parse data
    parsed_data = parse_inventory_data(json_data)
    
    # Save to CSV
    save_to_csv(parsed_data, args.output)

if __name__ == '__main__':
    main()