import cloudscraper
import requests

def download_manifest(app_id):
    scraper = cloudscraper.create_scraper()
    url = f"https://manifest.youngzm.com/api/download/{app_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://manifest.youngzm.com/"
    }
    response = scraper.get(url, headers=headers, timeout=30)
    
    # Strict validation for Steam Tools ZIPs
    if response.status_code == 200 and response.content.startswith(b'PK'):
        return response.content
    
    raise Exception(f"Faulty data received (Status: {response.status_code})")