import os, discord, asyncio, glob, shutil, time, requests, sys
from discord.ext import commands
from DrissionPage import ChromiumPage, ChromiumOptions

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- UTILITIES ---
def get_steam_id(query):
    """Instant Name-to-ID search via Steam Store API"""
    if query.isdigit(): return query
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
    try:
        r = requests.get(url, timeout=5)
        items = r.json().get('items', [])
        return str(items[0]['id']) if items else None
    except: return None

def upload_to_cloud(file_path):
    """Fallback for files over 25MB"""
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://catbox.moe/user/api.php", 
                             data={"reqtype": "fileupload"}, 
                             files={"fileToUpload": f}, timeout=60)
        return r.text if r.status_code == 200 else None
    except: return None

# --- BROWSER ENGINE ---
class FastEngine:
    def __init__(self):
        co = ChromiumOptions()
        co.headless(True)
        co.set_argument('--no-sandbox')            # Critical for Linux/Web Hosts
        co.set_argument('--disable-dev-shm-usage') # Prevents crashes on low-RAM hosts
        co.set_argument('--mute-audio')
        co.set_argument('--blink-settings=imagesEnabled=false')
        
        # Smart path detection for Windows OR Linux
        if sys.platform == "win32":
            paths = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', 
                     os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')]
            for p in paths:
                if os.path.exists(p): co.set_browser_path(p); break
        else:
            # Common paths for Railway, Render, and Linux VPS
            linux_paths = ['/usr/bin/google-chrome', '/usr/bin/chromium-browser', '/app/.apt/usr/bin/google-chrome']
            for p in linux_paths:
                if os.path.exists(p): co.set_browser_path(p); break

        self.page = ChromiumPage(co)
        self.page.set.load_strategy.eager()
        self.lock = asyncio.Lock()
        self.page.get(TARGET_SITE)

    def run_gen(self, app_id):
        job_id = int(time.time())
        work_dir = os.path.abspath(f"work_{app_id}_{job_id}")
        os.makedirs(work_dir, exist_ok=True)
        
        self.page.set.download_path(work_dir)
        self.page.run_js(f'document.getElementById("appId").value = "{app_id}";')
        self.page.run_js('downloadManifest();')

        final_path = None
        for _ in range(150): # 30s timeout
            time.sleep(0.2)
            zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) 
                    if not f.endswith('.crdownload') and not f.endswith('.tmp')]
            if zips:
                time.sleep(2) # Release file lock
                dest = os.path.abspath(f"Manifest_{app_id}_{job_id}.zip")
                shutil.move(zips[0], dest)
                final_path = dest
                break
        
        shutil.rmtree(work_dir, ignore_errors=True)
        return final_path

engine = None

@bot.command(name='gen')
async def gen(ctx, *, query: str = None):
    if not query: return await ctx.send(f"❓ {ctx.author.mention}, use `!gen [game name or ID]`")
    
    app_id = get_steam_id(query)
    if not app_id: return await ctx.send(f"❌ {ctx.author.mention}, could not find `{query}` on Steam.")

    msg = await ctx.send(f"⚡ {ctx.author.mention}, **Processing:** `{app_id}`...")

    async with engine.lock:
        start = time.perf_counter()
        file_path = await asyncio.to_thread(engine.run_gen, app_id)
        end = time.perf_counter()

    if file_path and os.path.exists(file_path):
        elapsed = round(end - start, 1)
        size = os.path.getsize(file_path)

        if size > 24 * 1024 * 1024: # 24MB Cloud Fallback
            await msg.edit(content=f"☁️ {ctx.author.mention}, file is too large for Discord. Uploading to Cloud...")
            url = await asyncio.to_thread(upload_to_cloud, file_path)
            if url:
                await ctx.send(f"🔔 {ctx.author.mention} **Link Ready!**\n🔗 {url}\n⏱️ Time: `{elapsed}s`")
                await msg.delete()
            else:
                await msg.edit(content=f"❌ {ctx.author.mention}, Cloud upload failed.")
        else:
            # Direct Ping and Upload
            await ctx.send(content=f"✅ {ctx.author.mention} **Manifest Ready!** (`{elapsed}s`)", 
                           file=discord.File(file_path))
            await msg.delete()
        
        os.remove(file_path)
    else:
        await msg.edit(content=f"❌ {ctx.author.mention}, generation timed out or the site failed.")

@bot.event
async def on_ready():
    global engine
    engine = FastEngine()
    print(f"🚀 Speed Bot Online: {bot.user}")

bot.run(TOKEN)
