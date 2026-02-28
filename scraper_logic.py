import time
import random
import cloudscraper
from curl_cffi import requests
from datetime import datetime

class NuclearSteamBot:
    def __init__(self, app_id):
        self.app_id = app_id
        self.url = f"https://raw.githubusercontent.com/SteamTools-Team/GameList/main/manifest/{app_id}.lua"
        self.log_file = "learning_log.txt"
        # Proxy format (Optional): 'http://user:pass@host:port'
        self.proxy = None 

    def _log(self, status, msg=""):
        t = datetime.now().strftime("%H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{t}] {status}: {msg}\n")

    def solve_and_fetch(self):
        print(f"🌀 Revamping strategy for AppID: {self.app_id}")
        
        # Strategy 1: The Cloudscraper Bypass (Handles JS Challenges)
        try:
            print("🚀 Strategy 1: Cloudscraper JS-Bypass...")
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            resp = scraper.get(self.url, timeout=20)
            
            if resp.status_code == 200:
                self._log("SUCCESS", "Bypassed via Cloudscraper")
                return resp.text
        except Exception as e:
            print(f"⚠️ Strategy 1 failed. Moving to Nuclear Fix...")

        # Strategy 2: Nuclear TLS Impersonation (Handles Handshake blocks)
        identities = ["chrome120", "safari15_5", "edge101", "chrome110"]
        for identity in identities:
            print(f"🔄 Strategy 2: Rotating to {identity}...")
            try:
                # Reset session to clear tracking cookies
                with requests.Session() as s:
                    proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
                    r = s.get(self.url, impersonate=identity, proxies=proxies, timeout=25)

                    if r.status_code == 200:
                        self._log("SUCCESS", f"Unblocked with {identity}")
                        return r.text
                    
                    if r.status_code == 404:
                        print("🛑 404: This AppID manifest does not exist.")
                        return None
                    
                    if r.status_code in [403, 429]:
                        print(f"❌ Still blocked ({r.status_code}). Learning... waiting...")
                        time.sleep(random.uniform(5, 10)) # Real human jitter
                        
            except Exception as e:
                self._log("ERROR", str(e))
        
        return None

if __name__ == "__main__":
    APP_ID = "367520" # Change to your ID
    bot = NuclearSteamBot(APP_ID)
    content = bot.solve_and_fetch()

    if content:
        with open(f"{APP_ID}.lua", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ FIXED: {APP_ID}.lua saved successfully!")
    else:
        print("\n💥 ALL BYPASSES FAILED. The site has likely banned your IP.")
        print("💡 Solution: Add a proxy to the 'self.proxy' line in the code.")
