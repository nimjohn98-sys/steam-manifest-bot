import os, discord, asyncio, glob, shutil, time, requests, sys
from discord.ext import commands
from DrissionPage import ChromiumPage, ChromiumOptions

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- FAILSAFE: STEAM SEARCH ---
def get_steam_id(query):
    if query.isdigit(): return query
    # Primary: Official Store Search
    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
        r = requests.get(url, timeout=5)
        items = r.json().get('items', [])
        if items: return str(items[0]['id'])
    except: pass
    
    # Secondary Fallback: Search Suggest API
    try:
        url = f"https://store.steampowered.com/api/searchsuggestions/?term={query}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            # Simple string search in response if JSON fails
            import re
            match = re.search(r'app/(\d+)', r.text)
            if match: return match.group(1)
    except: pass
    return None

# --- FAILSAFE: CLOUD UPLOAD ---
def upload_to_cloud(file_path):
    for attempt in range(2):
        try:
            with open(file_path, "rb") as f:
                r = requests.post("https://catbox.moe/user/api.php", 
                                 data={"reqtype": "fileupload"}, 
                                 files={"fileToUpload": f}, timeout=45)
            if r.status_code == 200 and "https" in r.text:
                return r.text
        except:
            time.sleep(2)
    return None

# --- FAILSAFE: BROWSER ENGINE ---
class WindowsEngine:
    def __init__(self):
        self.co = ChromiumOptions()
        self.setup_options()
        self.browser = None
        self.lock = asyncio.Lock()
        self.start_browser()

    def setup_options(self):
        paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe', 
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')
        ]
        for p in paths:
            if os.path.exists(p): 
                self.co.set_browser_path(p)
                break
        self.co.headless(True)
        self.co.set_argument('--mute-audio')
        self.co.set_argument('--blink-settings=imagesEnabled=false')
        self.co.set_argument('--disable-gpu')

    def start_browser(self):
        try:
            if self.browser: self.browser.quit()
            self.browser = ChromiumPage(self.co)
            self.browser.set.load_strategy.eager()
            self.browser.get(TARGET_SITE)
            print("🚀 Browser Engine Initialized.")
        except Exception as e:
            print(f"❌ Browser Start Failed: {e}")

    def run_gen(self, app_id):
        # Failsafe: Re-verify browser is alive
        try:
            if not self.browser or self.browser.tabs_count == 0:
                self.start_browser()
        except: self.start_browser()

        job_id = int(time.time())
        work_dir = os.path.abspath(f"win_job_{app_id}_{job_id}")
        os.makedirs(work_dir, exist_ok=True)
        
        try:
            self.browser.set.download_path(work_dir)
            self.browser.run_js(f'document.getElementById("appId").value = "{app_id}";')
            self.browser.run_js('downloadManifest();')

            final_path = None
            for _ in range(150): # 30s Wait
                time.sleep(0.2)
                zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) 
                        if not f.endswith('.crdownload') and not f.endswith('.tmp')]
                
                if zips:
                    # FAILSAFE: Ensure Windows has released the file lock
                    time.sleep(2) 
                    dest = os.path.abspath(f"Manifest_{app_id}_{job_id}.zip")
                    for _ in range(5): # Retry move if file busy
                        try:
                            shutil.move(zips[0], dest)
                            final_path = dest
                            break
                        except: time.sleep(1)
                    break
            
            return final_path
        finally:
            # Failsafe: Cleanup temp folder even if it crashes
            shutil.rmtree(work_dir, ignore_errors=True)

engine = None

@bot.command(name='gen')
async def gen(ctx, *, query: str = None):
    if not query: return await ctx.send(f"❓ {ctx.author.mention}, need a name or AppID.")
    
    app_id = get_steam_id(query)
    if not app_id: return await ctx.send(f"❌ {ctx.author.mention}, Steam couldn't find `{query}`.")

    msg = await ctx.send(f"⚡ {ctx.author.mention}, **Manifesting:** `{app_id}`...")

    async with engine.lock:
        try:
            start = time.perf_counter()
            file_path = await asyncio.to_thread(engine.run_gen, app_id)
            end = time.perf_counter()
            elapsed = round(end - start, 1)

            if file_path and os.path.exists(file_path):
                size = os.path.getsize(file_path)
                
                # Cloud Fallback if > 25MB
                if size > 24.5 * 1024 * 1024:
                    await msg.edit(content=f"☁️ {ctx.author.mention}, file is too big. Using Cloud Link...")
                    url = await asyncio.to_thread(upload_to_cloud, file_path)
                    if url:
                        await ctx.send(f"🔔 {ctx.author.mention} **Manifest Link Ready!**\n🔗 {url}\n⏱️ `{elapsed}s`")
                        await msg.delete()
                    else:
                        await msg.edit(content=f"❌ {ctx.author.mention}, Cloud upload failed for `{app_id}`.")
                else:
                    # Direct Send
                    await ctx.send(content=f"✅ {ctx.author.mention} **Manifest Ready!** (`{elapsed}s`)", 
                                   file=discord.File(file_path))
                    await msg.delete()
                
                # Failsafe: Wait before deletion to ensure upload finished
                await asyncio.sleep(5)
                if os.path.exists(file_path): os.remove(file_path)
            else:
                await msg.edit(content=f"❌ {ctx.author.mention}, generation timed out. Is the site down?")
        except Exception as e:
            await msg.edit(content=f"⚠️ {ctx.author.mention}, Internal Error: `{str(e)[:100]}`")

@bot.event
async def on_ready():
    global engine
    # Cleanup any leftovers from a crash
    for f in glob.glob("win_job_*"): shutil.rmtree(f, ignore_errors=True)
    for f in glob.glob("Manifest_*.zip"): os.remove(f)
    
    engine = WindowsEngine()
    print(f"🔥 Failsafe Bot Active: {bot.user}")

bot.run(TOKEN)
