#!/usr/bin/env python3

import argparse
import os
import requests
import zipfile
from pathlib import Path

def get_sec_headers():
    return {
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
    }

def download_sec_data(url: str, output_dir: str) -> str:
    headers = get_sec_headers()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract filename from URL
    zip_filename = os.path.join(output_dir, url.split('/')[-1])
    
    print(f"Downloading SEC data from {url}")
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    
    # Download the file
    with open(zip_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Download completed: {zip_filename}")
    return zip_filename

def unzip_file(zip_filename: str, extract_dir: str) -> str:
    print(f"Extracting {zip_filename} to {extract_dir}")
    
    # Create extract directory if it doesn't exist
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"Extraction completed to: {extract_dir}")
    return extract_dir

def main():
    parser = argparse.ArgumentParser(description='Download and extract SEC financial statement dataset')
    parser.add_argument('--url', required=True, help='URL of the SEC dataset zip file')
    parser.add_argument('--output', required=True, help='Output directory for the extracted files')
    
    args = parser.parse_args()
    
    try:
        # Download the zip file
        zip_filename = download_sec_data(args.url, args.output)
        
        # Create extraction directory
        extract_dir = os.path.join(args.output, Path(zip_filename).stem)
        
        # Extract the zip file
        unzip_file(zip_filename, extract_dir)
        
        # Remove the zip file after extraction
        os.remove(zip_filename)
        print(f"Cleaned up zip file: {zip_filename}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()