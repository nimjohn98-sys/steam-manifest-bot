import cloudscraper
import requests

def download_manifest(app_id):
    # Try Method 1: Cloudscraper
    scraper = cloudscraper.create_scraper()
    url = f"https://manifest.youngzm.com/api/download/{app_id}"
    r = scraper.get(url, timeout=15)
    
    if r.status_code == 200 and r.content.startswith(b'PK'):
        return r.content
    
    # Try Method 2: Manual Headers if Cloudscraper is blocked
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://manifest.youngzm.com/"}
    r = requests.get(url, headers=headers, timeout=15)
    
    if r.status_code == 200 and r.content.startswith(b'PK'):
        return r.content
        
    raise Exception(f"All bypass methods failed. Site returned code: {r.status_code}")