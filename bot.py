import os, discord, asyncio, json, random, shutil, glob, time
from discord.ext import commands
from DrissionPage import ChromiumPage, ChromiumOptions
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION (YOUR TOKEN INTEGRATED) ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

class SpeedEngine:
    def __init__(self):
        co = ChromiumOptions().set_browser_path(CHROME_PATH).headless(True)
        # SPEED TRICKS: Strip the browser to the bone
        co.set_argument('--blink-settings=imagesEnabled=false') # No images
        co.set_argument('--disable-gpu') # Save RAM/CPU
        co.set_argument('--disable-extensions')
        co.set_argument('--no-sandbox')
        co.set_argument('--mute-audio')
        
        self.page = ChromiumPage(co)
        self.page.set.load_strategy.eager() # Don't wait for ads/slow scripts
        self.lock = asyncio.Lock()

    def get_file(self, app_id):
        work_dir = os.path.join(os.getcwd(), f"tmp_{app_id}")
        if os.path.exists(work_dir): shutil.rmtree(work_dir)
        os.makedirs(work_dir)
        
        self.page.set.download_path(work_dir)
        self.page.get(TARGET_SITE)
        
        # Inject values directly into the site's JavaScript for instant triggering
        self.page.run_js(f'document.getElementById("appId").value = "{app_id}";')
        self.page.run_js('downloadManifest();')

        # Hyper-fast polling: Check for the file 5 times per second
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
    if not query: return await ctx.send("❓ Need a game name or ID.")
    
    # Simple check for ID or look in local cache (make sure steam_cache.json exists)
    app_id = query if query.isdigit() else "ERROR" 
    if app_id == "ERROR":
        await ctx.send("❌ Searching by name is slower. Try using the AppID directly!")
        return

    msg = await ctx.send(f"⚡ **Accelerating:** `{app_id}`...")

    async with engine.lock:
        start = time.time()
        path = await asyncio.to_thread(engine.get_file, app_id)
        elapsed = round(time.time() - start, 1)

    if path:
        await msg.edit(content=f"✅ **Generated in {elapsed}s!**")
        await ctx.send(file=discord.File(path))
        os.remove(path)
    else:
        await msg.edit(content="❌ Generation timed out.")

@bot.event
async def on_ready():
    global engine
    print("🚀 Pre-warming engine...")
    engine = SpeedEngine()
    print(f"✅ Bot Online: {bot.user}")

bot.run(TOKEN)
