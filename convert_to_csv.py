#!/usr/bin/env python3

import argparse
import csv
import os
from pathlib import Path


def convert_txt_to_csv(input_file: str, output_dir: str) -> str:
    """
    Convert a tab-delimited txt file to CSV format.
    
    Args:
        input_file: Path to the input txt file
        output_dir: Directory to save the CSV file
        
    Returns:
        Path to the created CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    input_path = Path(input_file)
    output_file = os.path.join(output_dir, f"{input_path.stem}.csv")
    
    with open(input_file, 'r', encoding='utf-8') as txt_file:
        # Read the first line to get headers
        headers = txt_file.readline().strip().split('\t')
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            
            # Process the rest of the file
            for line in txt_file:
                # Split by tabs and write to CSV
                row = line.strip().split('\t')
                writer.writerow(row)
    
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Convert SEC data txt files to CSV format')
    parser.add_argument('--input-dir', required=True, help='Directory containing the txt files')
    parser.add_argument('--output-dir', required=True, help='Directory to save the CSV files')
    
    args = parser.parse_args()
    
    # List of files to convert (excluding readme.htm)
    files_to_convert = ['num.txt', 'pre.txt', 'sub.txt', 'tag.txt']
    
    converted_files = []
    for filename in files_to_convert:
        input_file = os.path.join(args.input_dir, filename)
        if os.path.exists(input_file):
            print(f"Converting {filename} to CSV...")
            output_file = convert_txt_to_csv(input_file, args.output_dir)
            converted_files.append(output_file)
            print(f"Created {output_file}")
        else:
            print(f"Warning: {filename} not found in {args.input_dir}")
    
    print("\nConversion completed!")
    print("Converted files:")
    for file in converted_files:
        print(f"- {file}")


if __name__ == '__main__':
    main()