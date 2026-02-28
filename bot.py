import os
import discord
from discord.ext import commands
import asyncio
import time
import json
import random
import shutil
import glob
import requests
from concurrent.futures import ThreadPoolExecutor
from DrissionPage import ChromiumPage, ChromiumOptions

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
CACHE_FILE = "steam_cache.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
executor = ThreadPoolExecutor(max_workers=5)


class SteamResolver:
    def __init__(self):
        self.app_list_cache = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.load_local_cache()

    def load_local_cache(self):
        """Load from disk if the API fails"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.app_list_cache = json.load(f)
                print(f"📦 Loaded {len(self.app_list_cache)} games from local cache.")
            except:
                pass

    def refresh_cache(self):
        """Fetch official list and save locally"""
        try:
            url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
            r = requests.get(url, headers=self.headers, timeout=15)
            if r.status_code == 200 and "applist" in r.text:
                data = r.json()
                self.app_list_cache = data.get('applist', {}).get('apps', [])
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.app_list_cache, f)
                print(f"✅ Cache updated: {len(self.app_list_cache)} games.")
                return True
        except Exception as e:
            print(f"⚠️ API Fetch failed: {e}. Using local cache.")
        return False

    def get_id(self, query):
        if not query: return None
        if query.isdigit(): return query

        query_clean = query.lower().replace(" ", "")
        # Try exact match first
        for app in self.app_list_cache:
            if app['name'].lower() == query.lower():
                return str(app['appid'])
        # Try partial match
        for app in self.app_list_cache:
            if query_clean in app['name'].lower().replace(" ", ""):
                return str(app['appid'])
        return None


resolver = SteamResolver()


def process_request(query):
    app_id = resolver.get_id(query)
    if not app_id:
        return {"error": f"Game '{query}' not found. Try the AppID number instead."}

    job_id = random.randint(1000, 9999)
    work_dir = os.path.join(os.getcwd(), f"temp_{app_id}_{job_id}")
    os.makedirs(work_dir, exist_ok=True)

    co = ChromiumOptions().set_browser_path(CHROME_PATH).headless(True)
    co.set_argument('--no-first-run')
    page = ChromiumPage(co)
    page.set.download_path(work_dir)

    try:
        page.get(TARGET_SITE)
        page.run_js(f'document.getElementById("appId").value = "{app_id}";')
        page.run_js('downloadManifest();')

        for _ in range(120):  # 60 sec wait
            time.sleep(0.5)
            zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) if not f.endswith('.crdownload')]
            if zips:
                final_path = os.path.join(os.getcwd(), f"Manifest_{app_id}.zip")
                shutil.move(zips[0], final_path)
                return {"path": final_path, "id": app_id}
        return {"error": "Website timed out generating the file."}
    except Exception as e:
        return {"error": f"Browser Error: {str(e)}"}
    finally:
        page.quit()
        shutil.rmtree(work_dir, ignore_errors=True)


@bot.command(name='gen')
async def generate(ctx, *, query: str = None):
    if not query:
        return await ctx.send("❓ Usage: `!gen Game Name` or `!gen AppID`")

    msg = await ctx.send(f"🔍 **Searching:** `{query}`...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(executor, process_request, query)

    if "error" in res:
        await msg.edit(content=f"❌ **Error:** {res['error']}")
    else:
        await msg.edit(content=f"📦 **Success!** ID: `{res['id']}`. Sending...")
        await ctx.send(file=discord.File(res['path']))
        if os.path.exists(res['path']): os.remove(res['path'])


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    resolver.refresh_cache()


bot.run(TOKEN)
