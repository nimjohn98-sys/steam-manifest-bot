import os
import discord
from discord.ext import commands
import asyncio
import json
import requests
import random
import shutil
import glob
from DrissionPage import ChromiumPage, ChromiumOptions
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
TOKEN = "YOUR_DISCORD_BOT_TOKEN"
TARGET_SITE = "https://manifest.youngzm.com/"
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
PREFIX = "!"

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True  # MUST be enabled in Discord Developer Portal
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
executor = ThreadPoolExecutor(max_workers=5)

# --- STEAM RESOLVER (ID SEARCH) ---
class SteamResolver:
    def __init__(self):
        self.app_list_cache = []
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        self.load_cache()

    def load_cache(self):
        if os.path.exists("steam_cache.json"):
            with open("steam_cache.json", "r", encoding="utf-8") as f:
                self.app_list_cache = json.load(f)

    def refresh(self):
        try:
            r = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", headers=self.headers, timeout=10)
            if r.status_code == 200:
                self.app_list_cache = r.json().get('applist', {}).get('apps', [])
                with open("steam_cache.json", "w", encoding="utf-8") as f:
                    json.dump(self.app_list_cache, f)
                return True
        except: return False

    def get_id(self, query):
        if query.isdigit(): return query
        query = query.lower().replace(" ", "")
        for app in self.app_list_cache:
            if query in app['name'].lower().replace(" ", ""):
                return str(app['appid'])
        return None

resolver = SteamResolver()

# --- BROWSER ENGINE ---
def process_request(query):
    app_id = resolver.get_id(query)
    if not app_id: return {"error": "Game not found."}

    work_dir = os.path.join(os.getcwd(), f"temp_{app_id}_{random.randint(100,999)}")
    os.makedirs(work_dir, exist_ok=True)
    
    co = ChromiumOptions().set_browser_path(CHROME_PATH).headless(True)
    page = ChromiumPage(co)
    page.set.download_path(work_dir)

    try:
        page.get(TARGET_SITE)
        page.run_js(f'document.getElementById("appId").value = "{app_id}";')
        page.run_js('downloadManifest();')

        for _ in range(60): # Wait 30s
            time.sleep(0.5)
            zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) if not f.endswith('.crdownload')]
            if zips:
                final_name = f"Manifest_{app_id}.zip"
                shutil.move(zips[0], final_name)
                return {"path": final_name, "id": app_id}
        return {"error": "Timed out."}
    finally:
        page.quit()
        shutil.rmtree(work_dir, ignore_errors=True)

# --- BOT COMMANDS ---

@bot.command(name='info')
async def info_command(ctx):
    embed = discord.Embed(
        title="📖 Manifest Bot Guide",
        description="I generate Steam manifest files using Game Names or AppIDs.",
        color=discord.Color.green()
    )
    embed.add_field(
        name="🎮 How to use",
        value=f"Type `{PREFIX}gen [Game Name]`\nExample: `{PREFIX}gen Elden Ring`",
        inline=False
    )
    embed.add_field(
        name="🔢 How to find AppID",
        value="Look at the Steam Store URL: `store.steampowered.com/app/1245620/` \n→ The ID is **1245620**.",
        inline=False
    )
    embed.set_footer(text="Tip: If the name doesn't work, use the ID number directly.")
    await ctx.send(embed=embed)

@bot.command(name='gen')
async def gen_command(ctx, *, query: str = None):
    if not query:
        return await ctx.send(f"❓ Please provide a game name. Example: `{PREFIX}gen Portal 2`")

    msg = await ctx.send(f"⏳ **Generating manifest for:** `{query}`...")
    
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(executor, process_request, query)

    if "error" in res:
        await msg.edit(content=f"❌ **Error:** {res['error']}")
    else:
        await msg.edit(content=f"✅ **Success!** Sending AppID `{res['id']}`...")
        await ctx.send(file=discord.File(res['path']))
        if os.path.exists(res['path']): os.remove(res['path'])

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    resolver.refresh()

bot.run(TOKEN)
