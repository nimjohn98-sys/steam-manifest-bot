import urllib.request
import zipfile
import os

def download_and_extract(url, extract_folder='extracted_files'):
    """Downloads a ZIP file from a reliable URL, tests it, and extracts it safely."""
    
    # Create the target folder if it doesn't exist
    if not os.path.exists(extract_folder):
        os.makedirs(extract_folder)

    # Get the filename from the URL
    file_name = url.split('/')[-1]
    if not file_name.endswith('.zip'):
        file_name = 'downloaded_archive.zip'
        
    print(f"[*] Downloading {file_name} from official source...")
    
    # 1. Download the file
    try:
        urllib.request.urlretrieve(url, file_name)
        print("[+] Download complete!")
    except Exception as e:
        print(f"[-] Error downloading the file. Check your connection or the URL.\nDetails: {e}")
        return

    # 2. Verify and Extract
    print(f"[*] Testing and extracting archive...")
    try:
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            # Test the zip file for CRC errors before extracting
            bad_file = zip_ref.testzip()
            if bad_file:
                print(f"[-] WARNING: Corrupt file detected inside the archive: {bad_file}")
                print("[-] The archive might be faulty. Proceeding with caution...")
            
            # Extract everything
            zip_ref.extractall(extract_folder)
            print(f"[+] Success! All files securely extracted to the '{extract_folder}' folder.")
            
    except zipfile.BadZipFile:
        print("[-] FATAL ERROR: The downloaded file is completely invalid or severely corrupted.")
    except Exception as e:
        print(f"[-] An unexpected error occurred: {e}")

# ==========================================
# HOW TO USE IT:
# Replace the URL below with a safe, direct link to a ZIP file (like a GitHub release)
# ==========================================

target_url = 'https://github.com/psf/requests/archive/refs/heads/main.zip' 

download_and_extract(target_url)
