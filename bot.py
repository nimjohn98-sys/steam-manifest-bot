import os
import discord
from discord.ext import commands
import asyncio
import time
import re
import random
import shutil
import glob 
import requests 
from concurrent.futures import ThreadPoolExecutor
from DrissionPage import ChromiumPage, ChromiumOptions

# --- YOUR CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

# Standard Windows path for Chrome
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

# Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Performance: Handle up to 5 users simultaneously
executor = ThreadPoolExecutor(max_workers=5)

class WindowsSentinel:
    def get_options(self):
        """Optimized Windows Browser Settings"""
        co = ChromiumOptions()
        co.set_browser_path(CHROME_PATH)
        # Set a random port to allow multiple browsers to open at once
        co.set_local_port(random.randint(10000, 60000))
        co.headless(True) # Change to False if you want to watch it work
        
        # Windows Performance Flags
        co.set_argument('--no-first-run')
        co.set_argument('--force-device-scale-factor=1')
        co.set_argument('--disable-infobars')
        return co

    def resolve_appid(self, name):
        """Fast AppID lookup using Steam API"""
        if name.isdigit(): return name
        try:
            url = f"https://store.steampowered.com/api/storesearch/?term={name}"
            r = requests.get(url, timeout=5)
            data = r.json()
            if data['items']:
                return str(data['items'][0]['id'])
        except Exception:
            return None
        return None

engine = WindowsSentinel()

def process_request(query):
    """The Heavy-Lifting Worker Function"""
    app_id = engine.resolve_appid(query)
    if not app_id:
        return {"error": "Could not find an AppID for that game."}

    # Unique folder for this specific download
    job_id = random.randint(1000, 9999)
    work_dir = os.path.join(os.getcwd(), f"temp_job_{app_id}_{job_id}")
    os.makedirs(work_dir, exist_ok=True)

    # Initialize Browser
    page = ChromiumPage(engine.get_options())
    page.set.download_path(work_dir)

    try:
        page.get(TARGET_SITE)
        
        # Fast Javascript Injection
        page.run_js(f'document.getElementById("appId").value = "{app_id}";')
        page.run_js('downloadManifest();')

        # Poll for the ZIP file (max 60 seconds)
        for _ in range(120):
            time.sleep(0.5)
            # Find any .zip file that isn't currently downloading (.crdownload)
            zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) if not f.endswith('.crdownload')]
            if zips:
                final_zip = os.path.join(os.getcwd(), f"Manifest_{app_id}.zip")
                shutil.move(zips[0], final_zip)
                return {"path": final_zip, "id": app_id}
        
        return {"error": "Timed out waiting for the website to generate the ZIP."}

    except Exception as e:
        return {"error": f"Browser Error: {str(e)}"}
    finally:
        page.quit() # Always close browser to save RAM
        shutil.rmtree(work_dir, ignore_errors=True) # Cleanup temp folder

@bot.command(name='gen')
async def generate(ctx, *, query: str = None):
    if not query:
        await ctx.send("❓ Please provide a game name. Example: `!gen Elden Ring`")
        return

    status_msg = await ctx.send(f"🔍 **Searching:** `{query}`... (Allocating Windows Resources)")

    # Run the heavy processing in a separate thread so Discord doesn't lag
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, process_request, query)

    if "error" in result:
        await status_msg.edit(content=f"❌ **Error:** {result['error']}")
    else:
        await status_msg.edit(content=f"📦 **Success!** Found AppID: `{result['id']}`. Sending manifest...")
        await ctx.send(file=discord.File(result['path']))
        
        # Clean up the final file after sending
        if os.path.exists(result['path']):
            os.remove(result['path'])

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')
    print(f'🖥️ Windows Engine Status: ONLINE')

if __name__ == "__main__":
    bot.run(TOKEN)
