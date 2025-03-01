#!/usr/bin/env python3

import argparse
import os
import requests
import zipfile
from pathlib import Path

def download_sec_data(url: str, output_dir: str) -> None:
    """
    Download SEC financial dataset and unzip it to the specified directory.
    
    Args:
        url: The URL of the SEC financial dataset
        output_dir: Directory where the files should be extracted
    """
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

    try:
        # Download the file
        print(f"Downloading SEC data from {url}")
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        # Save the zip file
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Unzip the file
        print(f"Extracting files to {output_dir}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

        # Remove the zip file after extraction
        os.remove(zip_path)
        print("Download and extraction completed successfully")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
        raise
    except zipfile.BadZipFile as e:
        print(f"Error extracting the zip file: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Download SEC financial statement dataset')
    parser.add_argument('--url', type=str, required=True,
                      help='URL of the SEC financial dataset zip file')
    parser.add_argument('--output-dir', type=str, default='/tmp',
                      help='Directory to extract the files (default: /tmp)')

    args = parser.parse_args()
    download_sec_data(args.url, args.output_dir)

if __name__ == '__main__':
    main()