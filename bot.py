import os, discord, asyncio, glob, shutil, time, requests
from discord.ext import commands
from DrissionPage import ChromiumPage, ChromiumOptions

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

def get_steam_id(query):
    """Instant search via Steam API"""
    if query.isdigit(): return query
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
    try:
        r = requests.get(url, timeout=5)
        items = r.json().get('items', [])
        if items: return str(items[0]['id'])
    except: pass
    return None

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
        self.page.get(TARGET_SITE)

    def run_gen(self, app_id):
        # Unique folder for this specific request
        job_id = int(time.time())
        work_dir = os.path.abspath(f"work_{app_id}_{job_id}")
        os.makedirs(work_dir, exist_ok=True)
        
        self.page.set.download_path(work_dir)
        # Direct JS injection for speed
        self.page.run_js(f'document.getElementById("appId").value = "{app_id}";')
        self.page.run_js('downloadManifest();')

        final_path = None
        for _ in range(100): # 20 second timeout
            time.sleep(0.2)
            # Find the zip, but ignore partial downloads
            zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) 
                    if not f.endswith('.crdownload') and not f.endswith('.tmp')]
            
            if zips:
                time.sleep(1.5) # Critical pause for Windows file release
                dest_path = os.path.abspath(f"Manifest_{app_id}_{job_id}.zip")
                try:
                    shutil.move(zips[0], dest_path)
                    final_path = dest_path
                    break
                except Exception as e:
                    print(f"File move failed, retrying: {e}")
                    continue
        
        # Cleanup the temp work folder
        shutil.rmtree(work_dir, ignore_errors=True)
        return final_path

engine = None

@bot.command(name='gen')
async def gen(ctx, *, query: str = None):
    if not query: 
        return await ctx.send(f"❓ {ctx.author.mention}, please provide a game name.")
    
    app_id = get_steam_id(query)
    if not app_id: 
        return await ctx.send(f"❌ {ctx.author.mention}, couldn't find ID for `{query}`.")

    msg = await ctx.send(f"🚀 {ctx.author.mention}, manifesting ID: `{app_id}`...")
    
    async with engine.lock:
        start = time.perf_counter()
        file_path = await asyncio.to_thread(engine.run_gen, app_id)
        end = time.perf_counter()

    if file_path and os.path.exists(file_path):
        size = os.path.getsize(file_path)
        if size > 25 * 1024 * 1024:
            await msg.edit(content=f"⚠️ {ctx.author.mention}, file is too big for Discord (>{round(size/1048576, 1)}MB).")
            os.remove(file_path)
            return

        # Attempt to send with retry logic
        for attempt in range(3):
            try:
                await ctx.send(
                    content=f"📦 **Manifest Complete!** {ctx.author.mention}\n**Game ID:** `{app_id}`\n**Time:** `{round(end-start, 1)}s`",
                    file=discord.File(file_path)
                )
                await msg.delete()
                break
            except Exception as e:
                print(f"Upload attempt {attempt+1} failed: {e}")
                await asyncio.sleep(2)
        
        # Cleanup
        await asyncio.sleep(5) # Final wait before deleting from your PC
        if os.path.exists(file_path): os.remove(file_path)
    else:
        await msg.edit(content=f"❌ {ctx.author.mention}, the manifest site failed to respond.")

@bot.event
async def on_ready():
    global engine
    engine = FastBrowser()
    print(f"🔥 Bot Active: {bot.user}")

bot.run(TOKEN)
