import os
import discord
from discord.ext import commands
import asyncio
import time
import re
import subprocess
import random
import shutil
import glob 
import requests 
from concurrent.futures import ThreadPoolExecutor
from DrissionPage import ChromiumPage, ChromiumOptions

# --- ENCRYPTED CONFIG ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

# --- DYNAMIC SYSTEM DETECTION ---
def get_system_config():
    if os.getenv('RAILWAY_ENVIRONMENT'):
        # Linux / Railway Paths
        for path in ['/usr/bin/chromium', '/usr/bin/google-chrome', '/usr/bin/chromium-browser']:
            if os.path.exists(path): return path, True
        return "/usr/bin/chromium", True
    else:
        # Windows Path
        return r'C:\Program Files\Google\Chrome\Application\chrome.exe', False

CHROME_PATH, IS_LINUX = get_system_config()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
# MAX PERFORMANCE: Increase workers to saturate CPU/RAM
executor = ThreadPoolExecutor(max_workers=10)

class ApexEngine:
    def get_options(self):
        co = ChromiumOptions()
        co.set_browser_path(CHROME_PATH)
        co.set_local_port(random.randint(10000, 50000))
        co.headless(True)
        
        args = ['--no-sandbox', '--disable-gpu', '--no-first-run']
        if IS_LINUX:
            args += ['--disable-dev-shm-usage', '--single-process', '--no-zygote']
        else:
            args += ['--enable-aggressive-domstorage-flushing']
            
        for arg in args: co.set_argument(arg)
        return co

    def find_id_ultra(self, name):
        """Triple-threat search: API -> Store Scrape -> DB Scrape"""
        if name.isdigit(): return name
        try:
            r = requests.get(f"https://store.steampowered.com/api/storesearch/?term={name}", timeout=5)
            return str(r.json()['items'][0]['id'])
        except:
            # Fallback to web scrape if API is rate-limited
            try:
                temp_page = ChromiumPage(self.get_options())
                temp_page.get(f"https://steamdb.info/search/?a=app&q={name.replace(' ', '+')}")
                match = re.findall(r'/app/(\d+)', temp_page.html)
                temp_page.quit()
                return match[0] if match else None
            except: return None

engine = ApexEngine()

def overdrive_worker(query):
    app_id = engine.find_id_ultra(query)
    if not app_id: return {"error": "AppID not found."}

    page = ChromiumPage(engine.get_options())
    work_dir = os.path.join(os.getcwd(), f"job_{app_id}_{random.randint(1,999)}")
    os.makedirs(work_dir, exist_ok=True)
    page.set.download_path(work_dir)

    try:
        page.get(TARGET_SITE)
        # Fast Injection
        page.run_js(f'document.getElementById("appId").value = "{app_id}"; downloadManifest();')
        
        # Aggressive ZIP polling (0.5s intervals)
        for _ in range(120): # Wait up to 60 seconds for ZIP
            time.sleep(0.5)
            zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) if not f.endswith('.crdownload')]
            if zips:
                final_path = os.path.join(os.getcwd(), f"Manifest_Package_{app_id}.zip")
                shutil.move(max(zips, key=os.path.getctime), final_path)
                return {"path": final_path, "id": app_id}
        
        return {"error": "ZIP extraction timed out."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        page.quit()
        shutil.rmtree(work_dir, ignore_errors=True)

@bot.command(name='gen')
async def generate(ctx, *, query: str = None):
    if not query: return
    status = await ctx.send(f"🚀 **Sentinel Overdrive** processing `{query}`...")
    
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(executor, overdrive_worker, query)
    
    if "error" in res:
        await status.edit(content=f"🚨 **Critical Failure:** {res['error']}")
    else:
        await status.edit(content=f"✅ **Identity Locked:** `{res['id']}`. Sending ZIP bundle...")
        await ctx.send(file=discord.File(res['path']))
        os.remove(res['path'])

if __name__ == "__main__":
    bot.run(TOKEN)
