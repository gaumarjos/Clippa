import requests
from pathlib import Path
import time


def download_pdfs(start_id, end_id, output_dir):
    """
    Download PDF files from a range of IDs.

    Args:
        start_id: Starting ID number
        end_id: Ending ID number (inclusive)
        output_dir: Directory to save downloaded files
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0

    print(f"Starting download of PDFs from ID {start_id} to {end_id}")
    print(f"Output directory: {output_dir}\n")

    for pdf_id in range(start_id, end_id + 1):
        url = BASE_URL.format(pdf_id)
        filename = f"{pdf_id}_transcript_eng.pdf"
        filepath = Path(output_dir) / filename

        try:
            print(f"Downloading ID {pdf_id}... ", end="", flush=True)

            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                # Check if content is actually a PDF
                if response.headers.get('content-type', '').startswith('application/pdf'):
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ Success ({len(response.content)} bytes)")
                    success_count += 1
                else:
                    print(f"✗ Not a PDF (content-type: {response.headers.get('content-type')})")
                    fail_count += 1
            else:
                print(f"✗ Failed (HTTP {response.status_code})")
                fail_count += 1

        except requests.exceptions.RequestException as e:
            print(f"✗ Error: {e}")
            fail_count += 1

        # Be respectful to the server
        if pdf_id < end_id:
            time.sleep(DELAY_SECONDS)

    print(f"\n{'=' * 50}")
    print(f"Download complete!")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total: {success_count + fail_count}")
    print(f"{'=' * 50}")


# Configuration
START_ID = 1507
END_ID = 1532
BASE_URL = 'https://mip.api.medialivesystem.com/document/eclexiamipv2/attachments/{}/transcript_eng.pdf'
OUTPUT_DIR = '/Users/ste/Library/CloudStorage/OneDrive-POLIMIGSoM/6 Business Statistics/Transcript EN da clip IFLEX'
DELAY_SECONDS = 0.5  # Delay between requests to be respectful

if __name__ == "__main__":
    download_pdfs(START_ID, END_ID, OUTPUT_DIR)
