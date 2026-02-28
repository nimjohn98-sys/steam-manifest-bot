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

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

# --- DYNAMIC BROWSER DISCOVERY ---
def get_chrome_path():
    if os.getenv('RAILWAY_ENVIRONMENT'):
        # 1. Ask Linux where the command is
        for cmd in ['chromium', 'chromium-browser', 'google-chrome-stable', 'google-chrome']:
            path = shutil.which(cmd)
            if path: return path
        # 2. Check common Linux locations
        for path in ['/usr/bin/chromium', '/usr/bin/google-chrome', '/usr/bin/chromium-browser']:
            if os.path.exists(path): return path
        return "/usr/bin/chromium" # Last resort
    else:
        return r'C:\Program Files\Google\Chrome\Application\chrome.exe'

CHROME_PATH = get_chrome_path()
print(f"DEBUG: Sentinel Engine using browser at: {CHROME_PATH}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
executor = ThreadPoolExecutor(max_workers=10)

class SentinelEngine:
    def get_options(self):
        co = ChromiumOptions()
        co.set_browser_path(CHROME_PATH)
        co.set_local_port(random.randint(10000, 50000))
        co.headless(True)
        
        # Aggressive Linux Container Flags
        args = [
            '--no-sandbox',
            '--disable-dev-shm-usage', # FIXES RAILWAY CRASHES
            '--disable-gpu',
            '--no-zygote',
            '--remote-debugging-port=9222'
        ]
        for arg in args: co.set_argument(arg)
        return co

    def resolve_id(self, name):
        if name.isdigit(): return name
        try:
            r = requests.get(f"https://store.steampowered.com/api/storesearch/?term={name}", timeout=5)
            return str(r.json()['items'][0]['id'])
        except:
            return None

engine = SentinelEngine()

def process_worker(query):
    app_id = engine.resolve_id(query)
    if not app_id: return {"error": "AppID not found."}

    page = ChromiumPage(engine.get_options())
    work_dir = os.path.join(os.getcwd(), f"job_{app_id}_{random.randint(1,999)}")
    os.makedirs(work_dir, exist_ok=True)
    page.set.download_path(work_dir)

    try:
        page.get(TARGET_SITE)
        # Fast Injection
        page.run_js(f'document.getElementById("appId").value = "{app_id}"; downloadManifest();')
        
        # Wait up to 60s for ZIP
        for _ in range(120):
            time.sleep(0.5)
            zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) if not f.endswith('.crdownload')]
            if zips:
                dest = os.path.join(os.getcwd(), f"Package_{app_id}.zip")
                shutil.move(max(zips, key=os.path.getctime), dest)
                return {"path": dest, "id": app_id}
        
        return {"error": "ZIP generation timed out."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        page.quit()
        shutil.rmtree(work_dir, ignore_errors=True)

@bot.command(name='gen')
async def generate(ctx, *, query: str = None):
    if not query: return
    status = await ctx.send(f"🛡️ **Sentinel Engine** identifying `{query}`...")
    
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(executor, process_worker, query)
    
    if "error" in res:
        await status.edit(content=f"🚨 **Failure:** {res['error']}")
    else:
        await status.edit(content=f"✅ **ID `{res['id']}` Verified.** Sending ZIP...")
        await ctx.send(file=discord.File(res['path']))
        os.remove(res['path'])

if __name__ == "__main__":
    bot.run(TOKEN)
