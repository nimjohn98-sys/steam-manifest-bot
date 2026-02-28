import requests
import cloudscraper

def download_manifest(app_id):
    # DNA START - The bot will rewrite the values below
    target_url = f"https://manifest.youngzm.com/api/download/{app_id}"
    header_val = 'Mozilla/5.0'
    timeout_val = 15
    # DNA END
    
    # The bot toggles between requests and cloudscraper during evolution
    scraper = cloudscraper.create_scraper()
    
    response = scraper.get(target_url, headers={'User-Agent': header_val}, timeout=timeout_val)
    return response.content