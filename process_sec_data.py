#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from pathlib import Path


def process_num_file(input_file: str, output_file: str):
    """Process the numerical data file."""
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        # Read the first line to get headers
        headers = fin.readline().strip().split('\t')
        
        writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        
        # Process the rest of the lines
        for line in fin:
            fields = line.strip().split('\t')
            # Ensure we have all fields, pad with empty strings if needed
            fields.extend([''] * (len(headers) - len(fields)))
            writer.writerow(fields)


def process_pre_file(input_file: str, output_file: str):
    """Process the presentation information file."""
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        headers = fin.readline().strip().split('\t')
        
        writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        
        for line in fin:
            fields = line.strip().split('\t')
            fields.extend([''] * (len(headers) - len(fields)))
            writer.writerow(fields)


def process_sub_file(input_file: str, output_file: str):
    """Process the submission information file."""
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        headers = fin.readline().strip().split('\t')
        
        writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        
        for line in fin:
            fields = line.strip().split('\t')
            fields.extend([''] * (len(headers) - len(fields)))
            writer.writerow(fields)


def process_tag_file(input_file: str, output_file: str):
    """Process the tag definitions file."""
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        headers = fin.readline().strip().split('\t')
        
        writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        
        for line in fin:
            fields = line.strip().split('\t')
            fields.extend([''] * (len(headers) - len(fields)))
            writer.writerow(fields)


def main():
    parser = argparse.ArgumentParser(description='Process SEC financial statement data files into CSV format')
    parser.add_argument('input_dir', help='Directory containing the input files')
    parser.add_argument('output_dir', help='Directory to write the output CSV files')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process each file type
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # Map of input files to their processors
    file_processors = {
        'num.txt': process_num_file,
        'pre.txt': process_pre_file,
        'sub.txt': process_sub_file,
        'tag.txt': process_tag_file
    }
    
    for input_file, processor in file_processors.items():
        input_path = input_dir / input_file
        if input_path.exists():
            output_path = output_dir / input_file.replace('.txt', '.csv')
            print(f"Processing {input_file} to {output_path}")
            processor(str(input_path), str(output_path))
        else:
            print(f"Warning: {input_file} not found in {input_dir}", file=sys.stderr)


if __name__ == '__main__':
    main()