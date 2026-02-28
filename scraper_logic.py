import time
import random
import os
from datetime import datetime
from curl_cffi import requests
from bs4 import BeautifulSoup

class UnstoppableManifestBot:
    def __init__(self):
        # We start with a fresh session
        self.session = requests.Session()
        self.base_url = "https://raw.githubusercontent.com/SteamTools-Team/GameList/main/manifest/"
        # A wide range of modern browser identities to cycle through
        self.identities = ["chrome110", "chrome120", "safari15_5", "edge101", "safari_ios_16_0"]
        self.log_file = "learning_log.txt"

    def _log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def fetch_with_auto_fix(self, app_id):
        url = f"{self.base_url}{app_id}.lua"
        attempts = 0
        
        # This loop is the 'FIX'—it won't stop until success or exhausted identities
        while attempts < len(self.identities):
            identity = self.identities[attempts]
            print(f"🚀 [Attempt {attempts+1}] Using Identity: {identity}")

            try:
                # The CORE FIX: impersonate bypasses TLS fingerprinting
                response = self.session.get(url, impersonate=identity, timeout=20)

                if response.status_code == 200:
                    print(f"✅ UNBLOCKED: Manifest retrieved for AppID {app_id}")
                    self._log(f"SUCCESS: {app_id} unblocked with {identity}")
                    return response.text
                
                elif response.status_code == 404:
                    print(f"⚠️ 404: Manifest {app_id}.lua does not exist in this repo.")
                    return None

                elif response.status_code in [403, 429]:
                    # AUTO-FIX LOGIC:
                    print(f"❌ BLOCKED ({response.status_code}). Resetting session and rotating...")
                    self._log(f"BLOCK_DETECTED: {response.status_code} with {identity}")
                    
                    # 1. Clear cookies to remove 'tracked' session
                    self.session.cookies.clear()
                    
                    # 2. Add 'Human Jitter' (random wait)
                    wait_time = random.uniform(5, 10)
                    print(f"⏱️ Mimicking human pause... waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                    
                    # 3. Move to the next identity in the next loop
                    attempts += 1
                
            except Exception as e:
                print(f"💥 Connection Error: {e}. Trying next identity...")
                attempts += 1
                time.sleep(2)

        print("🛑 All automated fixes exhausted. Site may require a Proxy.")
        return None

# --- COPY & PASTE TO RUN ---
if __name__ == "__main__":
    # Your Target AppID (e.g., 367520 for Hollow Knight)
    APP_ID = "367520" 
    
    bot = UnstoppableManifestBot()
    manifest_data = bot.fetch_with_auto_fix(APP_ID)

    if manifest_data:
        # Save the result
        with open(f"{APP_ID}.lua", "w", encoding="utf-8") as f:
            f.write(manifest_data)
        print(f"\n💾 Manifest saved as {APP_ID}.lua")
        print("--- Manifest Preview ---")
        print(manifest_data[:150] + "...")
