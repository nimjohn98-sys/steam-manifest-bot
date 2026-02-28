import cloudscraper
import requests

def download_manifest(app_id):
    # Method 1: Cloudscraper bypass
    scraper = cloudscraper.create_scraper()
    url = f"https://manifest.youngzm.com/api/download/{app_id}"
    r = scraper.get(url, timeout=20)
    
    if r.status_code == 200 and r.content.startswith(b'PK'):
        return r.content
    
    # Method 2: Fallback (Spoofed Browser)
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://manifest.youngzm.com/"}
    r = requests.get(url, headers=headers, timeout=20)
    
    if r.status_code == 200 and r.content.startswith(b'PK'):
        return r.content
        
    raise Exception(f"All extraction methods failed. Site Status: {r.status_code}")
