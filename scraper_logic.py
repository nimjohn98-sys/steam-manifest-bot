import time
import random
import os
from datetime import datetime
from curl_cffi import requests
from bs4 import BeautifulSoup

class SteamManifestBot:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://raw.githubusercontent.com/SteamTools-Team/GameList/main/manifest/"
        self.log_file = "manifest_learning_log.txt"
        self.identities = ["chrome120", "safari15_5", "edge101"]

    def _log(self, app_id, status):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] AppID: {app_id} | Status: {status}\n")

    def fetch_mani_lua(self, app_id):
        """Fetches the .lua manifest for a specific Steam AppID."""
        # Standard naming convention for SteamTools Lua manifests
        url = f"{self.base_url}{app_id}.lua"
        
        print(f"🚀 Searching for Manifest: AppID {app_id}")
        
        for identity in self.identities:
            try:
                # FIX: Impersonating modern browsers to dodge GitHub/Cloudflare blocks
                response = self.session.get(url, impersonate=identity, timeout=15)
                
                if response.status_code == 200:
                    print(f"✅ SUCCESS: Lua Manifest found for {app_id}")
                    self._log(app_id, "SUCCESS")
                    return response.text
                
                elif response.status_code == 404:
                    print(f"⚠️ 404: Manifest not in this repository for AppID {app_id}.")
                    self._log(app_id, "NOT_FOUND")
                    return None
                
                elif response.status_code == 403:
                    print(f"❌ 403: Blocked. Learning and rotating identity...")
                    self._log(app_id, "BLOCKED_403")
                    time.sleep(2)
                
            except Exception as e:
                self._log(app_id, f"ERROR: {str(e)}")
        
        return None

# --- RUN BLOCK ---
if __name__ == "__main__":
    # Example: AppID for 'Hollow Knight' (367520) or your specific target
    APP_ID = "367520" 
    
    bot = SteamManifestBot()
    lua_content = bot.fetch_mani_lua(APP_ID)

    if lua_content:
        # Save the manifest locally
        filename = f"{APP_ID}.lua"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(lua_content)
        print(f"💾 File saved as: {filename}")
        print("-" * 30)
        print(lua_content[:200] + "...") # Preview the code
    else:
        print("\n❌ Could not retrieve Lua manifest.")
        print("💡 Tip: Ensure the AppID is correct or check the log file.")