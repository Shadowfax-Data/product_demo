import requests
import os

def download_pdf():
    url = "https://s26.q4cdn.com/463892824/files/doc_financials/2025/q3/efd1579f-72d2-4792-a227-b644f897276e.pdf"
    output_path = "/tmp/snowflake_quarterly_report.pdf"
    
    response = requests.get(url)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    print(f"PDF downloaded successfully to {output_path}")
    return output_path

if __name__ == "__main__":
    download_pdf()