#!/usr/bin/env python3

import argparse
import os
import pandas as pd
from typing import Dict, List
import sys
from tqdm import tqdm

def analyze_file(file_path: str, nrows: int = 50) -> Dict:
    """Analyze the first n rows of a file to understand its structure."""
    df = pd.read_csv(file_path, sep='\t', nrows=nrows)
    analysis = {
        'columns': list(df.columns),
        'dtypes': df.dtypes.to_dict(),
        'sample_rows': len(df),
        'total_rows': sum(1 for _ in open(file_path)) - 1  # Subtract header row
    }
    return analysis

def process_file(input_file: str, output_dir: str, chunk_size: int = 100000) -> None:
    """Process a tab-delimited file into CSV format using chunking for memory efficiency."""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}.csv")
    
    # Get total number of lines for progress bar
    total_rows = sum(1 for _ in open(input_file)) - 1  # Subtract header row
    
    # Process the file in chunks
    chunks = pd.read_csv(input_file, sep='\t', chunksize=chunk_size)
    first_chunk = True
    
    with tqdm(total=total_rows, desc=f"Processing {base_name}") as pbar:
        for chunk in chunks:
            # Write header only for the first chunk
            chunk.to_csv(output_file, 
                        mode='w' if first_chunk else 'a',
                        index=False,
                        header=first_chunk)
            first_chunk = False
            pbar.update(len(chunk))

def main():
    parser = argparse.ArgumentParser(description='Process SEC financial statement data files')
    parser.add_argument('--input-dir', default='/tmp/2024q4',
                       help='Directory containing the input files')
    parser.add_argument('--output-dir', default='/tmp/2024q4_processed',
                       help='Directory for output CSV files')
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Process each .txt file
    txt_files = [f for f in os.listdir(args.input_dir) if f.endswith('.txt')]
    
    print("Analyzing files structure...")
    file_analyses = {}
    for file_name in txt_files:
        input_file = os.path.join(args.input_dir, file_name)
        print(f"\nAnalyzing {file_name}:")
        analysis = analyze_file(input_file)
        file_analyses[file_name] = analysis
        print(f"Columns: {', '.join(analysis['columns'])}")
        print(f"Total rows: {analysis['total_rows']:,}")
        print(f"Data types: {analysis['dtypes']}")

    print("\nConverting files to CSV format...")
    for file_name in txt_files:
        input_file = os.path.join(args.input_dir, file_name)
        process_file(input_file, args.output_dir)

    print("\nProcessing complete. Files saved in:", args.output_dir)

if __name__ == '__main__':
    main()