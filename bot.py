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

# --- LINUX CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

# Linux standard path for Chromium (Railway/Ubuntu)
CHROME_PATH = "/usr/bin/chromium" 
if not os.path.exists(CHROME_PATH):
    # Fallback for alternative Linux distributions
    CHROME_PATH = "/usr/bin/google-chrome"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# HIGH-RESOURCE POOL: Maximize CPU/RAM utilization
MAX_WORKERS = 10 
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

class LinuxSentinel:
    def __init__(self):
        pass

    def kill_zombies(self):
        """Linux equivalent of taskkill. Purges hanging chromium processes."""
        try:
            # pkill is the standard Linux way to terminate processes by name
            subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
            subprocess.run(['pkill', '-f', 'chrome'], capture_output=True)
        except:
            pass

    def get_linux_options(self):
        co = ChromiumOptions()
        co.set_browser_path(CHROME_PATH)
        co.set_local_port(random.randint(10000, 40000))
        co.headless(True)
        
        # LINUX PERFORMANCE FLAGS
        arguments = [
            '--no-sandbox',            # Required for Docker/Railway
            '--disable-gpu',
            '--disable-dev-shm-usage', # Forces use of /tmp if /dev/shm is small
            '--disable-setuid-sandbox',
            '--no-first-run',
            '--no-zygote',             # Saves RAM by disabling the zygote process
            '--single-process'         # Lowers CPU overhead in containers
        ]
        for arg in arguments:
            co.set_argument(arg)
        return co

engine = LinuxSentinel()

def resolve_id_fast(name):
    """Direct API hit for AppID resolution."""
    if name.isdigit(): return name
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(f"https://store.steampowered.com/api/storesearch/?term={name}", headers=headers, timeout=5)
        return str(r.json()['items'][0]['id'])
    except:
        return None

def process_package(query):
    """The core Linux worker logic."""
    app_id = resolve_id_fast(query)
    if not app_id:
        return {"error": "AppID search failed."}

    # Initialize Linux Browser Instance
    options = engine.get_linux_options()
    page = ChromiumPage(options)
    
    # Isolated workspace
    work_dir = os.path.join(os.getcwd(), f"lnx_job_{app_id}_{random.randint(1,999)}")
    os.makedirs(work_dir, exist_ok=True)
    page.set.download_path(work_dir)

    try:
        page.get(TARGET_SITE)
        
        # Instant JS Execution
        page.run_js(f'''
            document.getElementById("appId").value = "{app_id}";
            downloadManifest();
        ''')
        
        # Aggressive ZIP Polling (Checks every 0.7s)
        for _ in range(70):
            time.sleep(0.7)
            zips = glob.glob(os.path.join(work_dir, "*.zip"))
            if zips and not any(f.endswith('.crdownload') for f in zips):
                dest = os.path.join(os.getcwd(), f"Steam_Package_{app_id}.zip")
                shutil.move(zips[0], dest)
                return {"path": dest, "id": app_id}
                
        return {"error": "Server-side ZIP generation timed out."}
    except Exception as e:
        return {"error": f"Linux Runtime Error: {str(e)}"}
    finally:
        page.quit()
        shutil.rmtree(work_dir, ignore_errors=True)

@bot.command(name='gen')
async def generate(ctx, *, query: str = None):
    if not query: return
    
    status = await ctx.send(f"🐧 **Linux Sentinel Engaged.** Allocating resources for `{query}`...")
    
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(executor, process_package, query)
    
    if "error" in res:
        await status.edit(content=f"🚨 **Linux System Failure:** {res['error']}")
    else:
        await status.edit(content=f"✅ **Package Captured.** [ID: `{res['id']}`]")
        await ctx.send(file=discord.File(res['path']))
        os.remove(res['path'])

if __name__ == "__main__":
    # Purge old processes on startup
    engine.kill_zombies()
    bot.run(TOKEN)
