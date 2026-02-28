import os, discord, asyncio, json, random, shutil, glob, time
from discord.ext import commands
from DrissionPage import ChromiumPage, ChromiumOptions
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

class SpeedEngine:
    def __init__(self):
        co = ChromiumOptions()
        
        # WINDOWS AUTO-DETECTION: Check common Chrome paths
        possible_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')
        ]
        
        found_path = None
        for path in possible_paths:
            if os.path.exists(path):
                found_path = path
                break
        
        if found_path:
            co.set_browser_path(found_path)
            print(f"✅ Found Chrome at: {found_path}")
        else:
            print("❌ ERROR: Chrome not found! Please install Google Chrome.")

        co.headless(True)
        co.set_argument('--mute-audio')
        co.set_argument('--blink-settings=imagesEnabled=false')
        
        self.page = ChromiumPage(co)
        self.page.set.load_strategy.eager()
        self.lock = asyncio.Lock()

    def get_file(self, app_id):
        work_dir = os.path.join(os.getcwd(), f"tmp_{app_id}")
        if os.path.exists(work_dir): shutil.rmtree(work_dir)
        os.makedirs(work_dir)
        
        self.page.set.download_path(work_dir)
        self.page.get(TARGET_SITE)
        
        # Inject values directly
        self.page.run_js(f'document.getElementById("appId").value = "{app_id}";')
        self.page.run_js('downloadManifest();')

        # Fast polling for Windows
        for _ in range(150): 
            time.sleep(0.2)
            zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) if not f.endswith('.crdownload')]
            if zips:
                final_path = f"Manifest_{app_id}.zip"
                shutil.move(zips[0], final_path)
                shutil.rmtree(work_dir)
                return final_path
        return None

engine = None

@bot.command(name='gen')
async def gen(ctx, *, query: str = None):
    if not query: return await ctx.send("❓ Give me an AppID.")
    if not query.isdigit(): return await ctx.send("❌ Please enter a numeric AppID for maximum speed.")

    msg = await ctx.send(f"⚡ **Generating:** `{query}`...")

    async with engine.lock:
        start = time.time()
        # Pass the request to the browser thread
        path = await asyncio.to_thread(engine.get_file, query)
        elapsed = round(time.time() - start, 1)

    if path:
        await msg.edit(content=f"✅ **Done in {elapsed}s!**")
        await ctx.send(file=discord.File(path))
        os.remove(path)
    else:
        await msg.edit(content="❌ Generation timed out.")

@bot.event
async def on_ready():
    global engine
    print("🚀 Initializing Windows Browser Engine...")
    engine = SpeedEngine()
    print(f"✅ Bot Ready: {bot.user}")

bot.run(TOKEN)
