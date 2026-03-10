import json
import os
import requests
from urllib.parse import quote, parse_qs, urlparse
import time
from http import cookies
from requests.utils import add_dict_to_cookiejar

def get_download_url(api_base_url, download_url_params, filename, session):
    """
    Request the actual download URL from the API.

    Args:
        api_base_url: Base API URL (e.g., 'https://www.gsom.polimi.it/api/dhub/get-download-url/')
        download_url_params: The downloadUrl from JSON (e.g., 'download?url=/sites/...')
        filename: The filename for the docs parameter
        session: requests.Session object with cookies
    """
    try:
        # Parse the parameters from the downloadUrl
        # Format: "download?url=/sites/.../file.docx&MasterUrl=/sites/..."
        if '?' in download_url_params:
            params_string = download_url_params.split('?', 1)[1]
            params = parse_qs(params_string)

            url_param = params.get('url', [''])[0]
            master_url_param = params.get('MasterUrl', [''])[0]

            # Construct the API request
            api_url = f"{api_base_url}?url={quote(url_param)}&MasterUrl={quote(master_url_param)}&filename={quote(filename)}&docs=true"

            # Make request to get the actual Azure Blob URL
            response = session.get(api_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data.get('success') and 'downloadUrl' in data:
                return data['downloadUrl']
            else:
                print(f"✗ API response missing downloadUrl: {data}")
                return None
        else:
            print(f"✗ Invalid downloadUrl format: {download_url_params}")
            return None

    except Exception as e:
        print(f"✗ Failed to get download URL: {str(e)}")
        return None

def download_file(url, filepath):
    """Download a file from URL to the specified filepath."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✓ Downloaded: {filepath}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {filepath}: {str(e)}")
        return False

def process_folder(folder_data, base_path, api_base_url, stats, session):
    """Recursively process folders and download files."""
    folder_name = folder_data.get('name', '')
    current_path = os.path.join(base_path, folder_name) if folder_name else base_path

    # Process files in current folder
    files = folder_data.get('files', [])
    for file_info in files:
        file_name = file_info.get('name', '')
        file_ext = os.path.splitext(file_name)[1].lower()

        # Only process PDF, DOC, and DOCX files
        if file_ext in ['.pdf', '.doc', '.docx']:
            stats['total'] += 1
            download_url_params = file_info.get('downloadUrl', '')

            if not download_url_params:
                print(f"⚠ Skipping {file_name}: No download URL found")
                stats['skipped'] += 1
                continue

            # Get the actual Azure Blob URL from the API
            print(f"→ Requesting URL for: {file_name}")
            actual_url = get_download_url(api_base_url, download_url_params, file_name, session)

            if actual_url:
                filepath = os.path.join(current_path, file_name)
                if download_file(actual_url, filepath):
                    stats['success'] += 1
                else:
                    stats['failed'] += 1

                # Small delay to avoid overwhelming the server
                time.sleep(0.5)
            else:
                print(f"✗ Could not get download URL for: {file_name}")
                stats['failed'] += 1

    # Recursively process subfolders
    subfolders = folder_data.get('folders', [])
    for subfolder in subfolders:
        process_folder(subfolder, current_path, api_base_url, stats, session)

def main(json_file, output_dir='downloaded_notes', api_base_url='', cookies=None):
    """Main function to process JSON and download files."""

    if not api_base_url:
        print("ERROR: API_BASE_URL is required!")
        return

    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        return

    # Get the root folder data
    root_data = data.get('data', {})

    if not root_data:
        print("No data found in JSON file")
        return

    # Create a session with cookies
    session = requests.Session()
    if cookies:
        session.cookies.update(cookies)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Statistics
    stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

    print(f"Starting download to: {output_dir}")
    print(f"API URL: {api_base_url}")
    print("-" * 50)

    # Process the root folder
    process_folder(root_data, output_dir, api_base_url, stats, session)

    print("-" * 50)
    print("Download complete!")
    print(f"\nStatistics:")
    print(f"  Total files found: {stats['total']}")
    print(f"  Successfully downloaded: {stats['success']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Skipped: {stats['skipped']}")





if __name__ == "__main__":
    # Configuration
    JSON_FILE = 'source_jsons/IFLEX_PM_documents.json'
    # OUTPUT_DIR = '/Users/ste/Library/CloudStorage/OneDrive-POLIMIGSoM/6 Business Statistics/Transcripts/Originals'
    OUTPUT_DIR = '/Users/ste/Downloads'
    API_BASE_URL = 'https://www.gsom.polimi.it/api/dhub/get-download-url/'

    print("POLIMI GSOM FLOW Document Downloader")
    print("=" * 50)

    # Load cookies from file and parse
    with open("cookies.txt", "r") as f:
        cookie_string = f.read().strip()
    cookie_jar = cookies.SimpleCookie()
    cookie_jar.load(cookie_string)  # Parses the string into a Morsel dict-like object [web:11][web:13]
    cookie_dict = {key: morsel.value for key, morsel in cookie_jar.items()}  # Convert to plain dict [web:7]

    main(JSON_FILE, OUTPUT_DIR, API_BASE_URL, cookie_dict)
