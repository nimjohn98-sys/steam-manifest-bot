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

class SpeedEngine:
    def __init__(self):
        co = ChromiumOptions()
        # FIX: No hardcoded Windows path. DrissionPage finds Linux Chrome automatically.
        co.headless(True)
        co.set_argument('--no-sandbox')            # Required for Linux servers
        co.set_argument('--disable-dev-shm-usage') # Prevents memory crashes on VPS
        co.set_argument('--blink-settings=imagesEnabled=false')
        
        try:
            self.page = ChromiumPage(co)
            self.page.set.load_strategy.eager()
            self.lock = asyncio.Lock()
            print("🚀 Linux Browser Engine Started.")
        except Exception as e:
            print(f"❌ Browser Error: {e}")
            self.lock = asyncio.Lock()

engine = None

@bot.command(name='gen')
async def gen(ctx, *, query: str = None):
    if not query: return await ctx.send("❓ Give me a name or AppID.")
    app_id = query if query.isdigit() else "ERROR" 
    
    # Optional: Logic to find ID from name could go here
    if app_id == "ERROR":
        return await ctx.send("❌ Use the AppID (e.g. `!gen 1245620`) for now.")

    msg = await ctx.send(f"⚡ **Generating:** `{app_id}`...")

    async with engine.lock:
        start = time.time()
        path = await asyncio.to_thread(self_get_file, app_id)
        elapsed = round(time.time() - start, 1)

    if path:
        await msg.edit(content=f"✅ Done in {elapsed}s!")
        await ctx.send(file=discord.File(path))
        os.remove(path)
    else:
        await msg.edit(content="❌ Timeout.")

def self_get_file(app_id):
    work_dir = os.path.join(os.getcwd(), f"tmp_{app_id}")
    os.makedirs(work_dir, exist_ok=True)
    engine.page.set.download_path(work_dir)
    engine.page.get(TARGET_SITE)
    engine.page.run_js(f'document.getElementById("appId").value = "{app_id}";')
    engine.page.run_js('downloadManifest();')
    for _ in range(100):
        time.sleep(0.3)
        zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip"))]
        if zips:
            final = f"Manifest_{app_id}.zip"
            shutil.move(zips[0], final)
            return final
    return None

@bot.event
async def on_ready():
    global engine
    engine = SpeedEngine()
    print(f"✅ Bot Online as {bot.user}")

bot.run(TOKEN)
