import argparse
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Set
import json

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def analyze_file(file_path: str, nrows: int = 50) -> Dict:
    """
    Analyze a tab-delimited text file and return its characteristics.
    """
    df = pd.read_csv(file_path, sep='\t', nrows=nrows)
    
    analysis = {
        'columns': [],
        'row_count': len(df),
        'sample_values': {}
    }
    
    for column in df.columns:
        col_info = {
            'name': column,
            'dtype': str(df[column].dtype),
            'unique_values': len(df[column].unique()),
            'null_count': df[column].isnull().sum(),
            'sample_values': df[column].dropna().head(5).tolist()
        }
        analysis['columns'].append(col_info)
    
    return analysis

def main():
    parser = argparse.ArgumentParser(description='Analyze SEC financial statement data files')
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing the input files')
    parser.add_argument('--output_file', type=str, required=True, help='Output JSON file for analysis results')
    args = parser.parse_args()

    files_to_analyze = ['num.txt', 'pre.txt', 'sub.txt', 'tag.txt']
    analysis_results = {}

    for file_name in files_to_analyze:
        file_path = os.path.join(args.input_dir, file_name)
        if os.path.exists(file_path):
            print(f"Analyzing {file_name}...")
            analysis_results[file_name] = analyze_file(file_path)
        else:
            print(f"Warning: {file_name} not found in {args.input_dir}")

    # Save analysis results to JSON file
    with open(args.output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2, cls=NumpyEncoder)
    
    print(f"\nAnalysis complete. Results saved to {args.output_file}")

if __name__ == "__main__":
    main()