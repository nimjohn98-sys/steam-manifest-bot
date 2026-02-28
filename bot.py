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

# --- HIGH-PERFORMANCE CONFIG ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

# --- ADAPTIVE PATHING ---
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None
CHROME_PATH = "/usr/bin/chromium" if IS_RAILWAY else r'C:\Program Files\Google\Chrome\Application\chrome.exe'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# RAM-HEAVY POOL: Increasing max_workers forces more CPU/RAM usage for speed
# Set this to 10 or 20 if you have 16GB+ RAM
MAX_WORKERS = 15 
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

class OverdriveEngine:
    def __init__(self):
        self.active_instances = {}

    def get_options(self):
        co = ChromiumOptions()
        co.set_browser_path(CHROME_PATH)
        co.set_local_port(random.randint(10000, 60000))
        
        # SPEED TRADEOFF: We disable "headless" to save CPU, 
        # but keep it True for Railway/Server stability.
        co.headless(True)
        
        # RAM OVERDRIVE: We remove limits on disk cache and memory usage
        # This allows Chrome to use as much RAM as it wants to render faster
        arguments = [
            '--no-sandbox',
            '--disable-gpu',
            '--disable-infobars',
            '--start-maximized',
            '--no-first-run',
            '--force-device-scale-factor=1',
            '--disable-dev-shm-usage' if IS_RAILWAY else '--enable-aggressive-domstorage-flushing'
        ]
        for arg in arguments: co.set_argument(arg)
        return co

    def resolve_id_lightning(self, name):
        """Ultra-fast ID resolution using simultaneous API hits."""
        if name.isdigit(): return name
        # Layer 1: Fastest API
        try:
            r = requests.get(f"https://store.steampowered.com/api/storesearch/?term={name}", timeout=3)
            return str(r.json()['items'][0]['id'])
        except:
            return None

engine = OverdriveEngine()

def fast_process(query):
    """The high-speed core logic."""
    app_id = engine.resolve_id_lightning(query)
    if not app_id: return {"error": "AppID Not Found."}

    # Create local instance (uses significant RAM)
    page = ChromiumPage(engine.get_options())
    
    work_dir = os.path.join(os.getcwd(), f"fast_job_{app_id}_{random.randint(1,1000)}")
    os.makedirs(work_dir, exist_ok=True)
    page.set.download_path(work_dir)

    try:
        # Load site with zero-wait strategy
        page.get(TARGET_SITE)
        
        # Injected JS is faster than waiting for DOM elements to 'appear'
        page.run_js(f'''
            document.getElementById("appId").value = "{app_id}";
            downloadManifest();
        ''')
        
        # Aggressive polling: checking every 0.5s instead of 1.0s
        for _ in range(60):
            time.sleep(0.5)
            # Prioritize ZIP packages
            zips = glob.glob(os.path.join(work_dir, "*.zip"))
            if zips and not any(f.endswith('.crdownload') for f in zips):
                dest = os.path.join(os.getcwd(), f"FINAL_{app_id}.zip")
                shutil.move(zips[0], dest)
                return {"path": dest, "id": app_id}
                
        return {"error": "Timed out waiting for ZIP generation."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        page.quit() # Close browser to release RAM after task
        shutil.rmtree(work_dir, ignore_errors=True)

@bot.command(name='gen')
async def generate(ctx, *, query: str = None):
    if not query: return
    
    msg = await ctx.send(f"🚀 **Overdrive Mode Engaged.** Allocating resources for `{query}`...")
    
    loop = asyncio.get_running_loop()
    # Pushing the task into our high-worker executor pool
    res = await loop.run_in_executor(executor, fast_process, query)
    
    if "error" in res:
        await msg.edit(content=f"🚨 **Overdrive Failure:** {res['error']}")
    else:
        await msg.edit(content=f"✅ **Package Secured.** (AppID: `{res['id']}`)")
        await ctx.send(file=discord.File(res['path']))
        os.remove(res['path'])

if __name__ == "__main__":
    # FAILSAFE: Kill all ghost chromes before start to clear RAM
    if not IS_RAILWAY:
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'], capture_output=True)
    bot.run(TOKEN)
