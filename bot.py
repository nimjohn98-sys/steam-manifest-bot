import os, discord, asyncio, json, random, shutil, glob, time, requests
from discord.ext import commands
from DrissionPage import ChromiumPage, ChromiumOptions
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
executor = ThreadPoolExecutor(max_workers=5)

class SteamResolver:
    def __init__(self):
        self.cache_file = "steam_cache.json"
        self.apps = []
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self.apps = json.load(f)
        else:
            self.refresh_cache()

    def refresh_cache(self):
        try:
            r = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", timeout=10)
            self.apps = r.json().get('applist', {}).get('apps', [])
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.apps, f)
        except: print("⚠️ Using existing cache (Steam API unreachable)")

    def find_id(self, query):
        if query.isdigit(): return query
        q = query.lower().strip().replace(" ", "")
        # Priority 1: Exact Match (Fast)
        for app in self.apps:
            if app['name'].lower().replace(" ", "") == q:
                return str(app['appid'])
        # Priority 2: Contains Match
        for app in self.apps:
            if q in app['name'].lower().replace(" ", ""):
                return str(app['appid'])
        return None

class FastBrowser:
    def __init__(self):
        co = ChromiumOptions()
        # Auto-detect Windows Chrome
        paths = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', 
                 r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe']
        for p in paths:
            if os.path.exists(p): co.set_browser_path(p); break
        
        co.headless(True)
        co.set_argument('--mute-audio')
        co.set_argument('--blink-settings=imagesEnabled=false') # SPEED: No images
        self.page = ChromiumPage(co)
        self.page.set.load_strategy.eager() # SPEED: Don't wait for ads/CSS
        self.lock = asyncio.Lock()

    def run_gen(self, app_id):
        work_dir = os.path.join(os.getcwd(), f"tmp_{app_id}_{random.randint(1,999)}")
        os.makedirs(work_dir, exist_ok=True)
        self.page.set.download_path(work_dir)
        
        # SPEED: Reuse the same tab instead of opening new ones
        self.page.get(TARGET_SITE)
        
        # SPEED: Use JS to bypass the form and trigger the download instantly
        self.page.run_js(f'document.getElementById("appId").value = "{app_id}";')
        self.page.run_js('downloadManifest();')

        # SPEED: Polling every 0.2s instead of 1s
        for _ in range(100):
            time.sleep(0.2)
            zips = glob.glob(os.path.join(work_dir, "*.zip"))
            if zips:
                final_name = f"Manifest_{app_id}.zip"
                shutil.move(zips[0], final_name)
                shutil.rmtree(work_dir)
                return final_name
        return None

resolver = SteamResolver()
engine = None

@bot.command(name='gen')
async def gen(ctx, *, query: str = None):
    if not query: return await ctx.send("❓ Give me a name (e.g. `!gen Elden Ring`)")
    
    app_id = resolver.find_id(query)
    if not app_id: return await ctx.send(f"❌ Could not find a Steam ID for `{query}`")

    status_msg = await ctx.send(f"🚀 **Target Lock:** `{query}` (ID: {app_id})...")
    
    async with engine.lock:
        start = time.perf_counter()
        file_path = await asyncio.to_thread(engine.run_gen, app_id)
        end = time.perf_counter()

    if file_path:
        await status_msg.edit(content=f"✅ **Manifest Ready!** (Speed: {round(end-start, 2)}s)")
        await ctx.send(file=discord.File(file_path))
        os.remove(file_path)
    else:
        await status_msg.edit(content="❌ The website failed to generate the file.")

@bot.event
async def on_ready():
    global engine
    engine = FastBrowser()
    print(f"🔥 Windows Speed Bot Online as {bot.user}")

bot.run(TOKEN)
