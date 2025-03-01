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

def download_file(url: str, output_dir: str) -> str:
    headers = get_sec_headers()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the filename from the URL
    zip_filename = os.path.join(output_dir, url.split('/')[-1])
    
    print(f"Downloading {url} to {zip_filename}")
    
    # Download with progress indication
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    downloaded = 0
    
    with open(zip_filename, 'wb') as f:
        for data in response.iter_content(block_size):
            downloaded += len(data)
            f.write(data)
            done = int(50 * downloaded / total_size)
            print(f"\rDownload progress: [{'=' * done}{' ' * (50-done)}] {downloaded}/{total_size} bytes", end='')
    
    print("\nDownload completed!")
    return zip_filename

def extract_zip(zip_path: str, extract_dir: str) -> str:
    print(f"\nExtracting {zip_path} to {extract_dir}")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Get the directory where files were extracted
    extract_path = os.path.join(extract_dir, Path(zip_path).stem)
    print(f"Files extracted to: {extract_dir}")
    
    return extract_dir

def main():
    parser = argparse.ArgumentParser(description='Download and extract SEC financial statement dataset')
    parser.add_argument('url', help='URL of the SEC dataset zip file')
    parser.add_argument('--output', '-o', default='/tmp',
                      help='Output directory for downloaded and extracted files (default: /tmp)')
    
    args = parser.parse_args()
    
    try:
        # Download the file
        zip_path = download_file(args.url, args.output)
        
        # Extract the zip file
        extract_path = extract_zip(zip_path, args.output)
        
        # List extracted files
        print("\nExtracted files:")
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                print(f"- {file}")
                
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        exit(1)
    except zipfile.BadZipFile as e:
        print(f"Error extracting zip file: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()