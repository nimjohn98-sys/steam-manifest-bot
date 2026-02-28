import cloudscraper
import requests

def download_manifest(app_id):
    """
    Specifically targets Steam Tools compatible ManiLua/Manifest formats.
    """
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    
    # Primary Endpoint for Steam Tools manifests
    # Note: If the site moves to api/v3, change it here on GitHub.
    url = f"https://manifest.youngzm.com/api/download/{app_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/octet-stream, application/zip, application/x-lua",
        "Referer": "https://manifest.youngzm.com/"
    }

    try:
        response = scraper.get(url, headers=headers, timeout=25)
        
        # Steam Tools manifests are often ZIPs or raw LUA files
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Check for ZIP header (PK) or LUA content
            if response.content.startswith(b'PK') or b'return' in response.content:
                return response.content
            else:
                raise Exception("Received 200 but file content is not a valid manifest/ZIP.")
                
        elif response.status_code == 403:
            raise Exception("Cloudflare 403: Site is in 'Under Attack' mode. Update required.")
        else:
            raise Exception(f"SteamTools Site Error: {response.status_code}")

    except Exception as e:
        # Fallback to direct requests if Cloudscraper fails
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.content
        raise e
