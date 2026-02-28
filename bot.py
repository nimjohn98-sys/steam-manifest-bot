import os, discord, asyncio, glob, shutil, time, requests
from discord.ext import commands
from DrissionPage import ChromiumPage, ChromiumOptions

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- STEAM STORE SEARCH ---
def get_steam_id(query):
    if query.isdigit(): return query
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
    try:
        r = requests.get(url, timeout=5)
        items = r.json().get('items', [])
        if items: 
            return str(items[0]['id'])
    except:
        pass
    return None

# --- BROWSER ENGINE ---
class FastBrowser:
    def __init__(self):
        co = ChromiumOptions()
        paths = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', 
                 r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe']
        for p in paths:
            if os.path.exists(p): 
                co.set_browser_path(p)
                break
        
        co.headless(True)
        co.set_argument('--mute-audio')
        co.set_argument('--blink-settings=imagesEnabled=false') 
        self.page = ChromiumPage(co)
        self.page.set.load_strategy.eager() 
        self.lock = asyncio.Lock()
        
        # Pre-load the site once
        self.page.get(TARGET_SITE)

    def run_gen(self, app_id):
        # Use absolute paths to prevent Windows folder confusion
        work_dir = os.path.abspath(f"tmp_{app_id}_{int(time.time())}")
        os.makedirs(work_dir, exist_ok=True)
        self.page.set.download_path(work_dir)
        
        self.page.run_js(f'document.getElementById("appId").value = "{app_id}";')
        self.page.run_js('downloadManifest();')

        final_path = None
        # Check every 0.2s for up to 30 seconds
        for _ in range(150): 
            time.sleep(0.2)
            
            # 1. If Chrome is still downloading, wait.
            if glob.glob(os.path.join(work_dir, "*.crdownload")) or glob.glob(os.path.join(work_dir, "*.tmp")):
                continue
                
            # 2. If the pure .zip is here, the download is completely finished.
            zips = glob.glob(os.path.join(work_dir, "*.zip"))
            if zips:
                final_path = os.path.abspath(f"Manifest_{app_id}.zip")
                shutil.move(zips[0], final_path)
                break # Exit the loop immediately
        
        shutil.rmtree(work_dir, ignore_errors=True)
        return final_path

engine = None

@bot.command(name='gen')
async def gen(ctx, *, query: str = None):
    if not query: 
        return await ctx.send("❓ Give me a name (e.g. `!gen Elden Ring`)")
    
    app_id = get_steam_id(query)
    if not app_id: 
        return await ctx.send(f"❌ Steam couldn't find a game matching `{query}`.")

    msg = await ctx.send(f"🚀 **Fetching Manifest for ID:** `{app_id}`...")
    
    async with engine.lock:
        start = time.perf_counter()
        file_path = await asyncio.to_thread(engine.run_gen, app_id)
        end = time.perf_counter()

    if file_path:
        # Check file size before trying to upload
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 25:
            await msg.edit(content=f"❌ **Error:** The manifest is {file_size_mb:.1f}MB. Discord bots can only upload files up to 25MB.")
            os.remove(file_path)
            return

        try:
            await msg.edit(content=f"✅ **Manifest Ready!** Uploading to Discord... (Took {round(end-start, 2)}s)")
            await ctx.send(file=discord.File(file_path))
        except Exception as e:
            # If Discord rejects it, tell us exactly why
            await ctx.send(f"❌ **Discord API Error:** Could not send the file. Details: `{e}`")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        await msg.edit(content="❌ The website timed out or failed to generate the zip file.")

@bot.event
async def on_ready():
    global engine
    engine = FastBrowser()
    print(f"🔥 Online as {bot.user}")

bot.run(TOKEN)
