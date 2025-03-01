#!/usr/bin/env python3

import argparse
import os
import requests
import zipfile
from tqdm import tqdm

def download_sec_data(url, output_dir):
    headers = {
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
    }

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, 'sec_data.zip')

    # Download the file with progress bar
    print(f"Downloading from {url}...")
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))

    with open(zip_path, 'wb') as f, tqdm(
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            pbar.update(size)

    # Extract the zip file
    print("Extracting files...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    # Remove the zip file
    os.remove(zip_path)
    print(f"Files extracted to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Download and extract SEC financial statement dataset')
    parser.add_argument('url', help='URL of the SEC dataset')
    parser.add_argument('--output-dir', default='/tmp/2024q4', help='Output directory for extracted files')
    args = parser.parse_args()

    download_sec_data(args.url, args.output_dir)

if __name__ == '__main__':
    main()