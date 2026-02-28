
import cloudscraper
def download_manifest(app_id):
    # Auto-generated fix for 403
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    url = f"https://manifest.youngzm.com/api/download/{app_id}"
    r = scraper.get(url)
    return r.content
