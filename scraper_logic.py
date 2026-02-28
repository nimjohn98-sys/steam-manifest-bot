import cloudscraper
def download_manifest(app_id):
    s = cloudscraper.create_scraper()
    r = s.get(f'https://manifest.youngzm.com/api/download/{app_id}')
    return r.content