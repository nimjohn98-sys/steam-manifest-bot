import os, discord, asyncio, glob, shutil, time, requests, sys
from discord.ext import commands
from DrissionPage import ChromiumPage, ChromiumOptions

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- RECOVERY ENGINE ---
class AutonomousEngine:
    def __init__(self):
        self.browser = None
        self.lock = asyncio.Lock()
        self.last_error = "None"
        self.start_engine()

    def start_engine(self):
        """Self-Correction: Cleans environment and reboots Chrome."""
        try:
            # FIX 1: Wipe zombie Chrome processes that lock the driver
            if sys.platform == "win32":
                os.system("taskkill /f /im chrome.exe /t >nul 2>&1")
                os.system("taskkill /f /im chromedriver.exe /t >nul 2>&1")

            # FIX 2: Clear old work folders to prevent name collisions
            for folder in glob.glob("win_job_*"):
                shutil.rmtree(folder, ignore_errors=True)

            co = ChromiumOptions()
            paths = [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe', 
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')
            ]
            for p in paths:
                if os.path.exists(p): 
                    co.set_browser_path(p)
                    break

            co.headless(True)
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-gpu')
            co.set_argument('--blink-settings=imagesEnabled=false')
            
            self.browser = ChromiumPage(co)
            self.browser.set.load_strategy.eager()
            self.browser.get(TARGET_SITE)
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    async def safe_run(self, app_id):
        """Attempts the task; if it fails, it resets and returns 'RETRY'."""
        try:
            if not self.browser: self.start_engine()

            job_id = int(time.time())
            work_dir = os.path.abspath(f"win_job_{app_id}_{job_id}")
            os.makedirs(work_dir, exist_ok=True)
            
            self.browser.set.download_path(work_dir)
            self.browser.run_js(f'document.getElementById("appId").value = "{app_id}";')
            self.browser.run_js('downloadManifest();')

            for _ in range(120): # 24 second timeout
                await asyncio.sleep(0.2)
                zips = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) if not f.endswith('.crdownload')]
                if zips:
                    await asyncio.sleep(1.5)
                    dest = os.path.abspath(f"Manifest_{app_id}_{job_id}.zip")
                    shutil.move(zips[0], dest)
                    return dest
            return None
        except Exception as e:
            self.last_error = str(e)
            self.start_engine() # Reboot on any error
            return "RETRY"
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

engine = None

@bot.command(name='gen')
async def gen(ctx, *, query: str = None):
    if not query: return await ctx.send(f"❓ {ctx.author.mention}, provide a game name.")
    
    app_id = await asyncio.to_thread(get_steam_id, query)
    if not app_id: return await ctx.send(f"❌ {ctx.author.mention}, couldn't find `{query}`.")

    msg = await ctx.send(f"⚡ {ctx.author.mention}, processing `{app_id}`...")

    async with engine.lock:
        result = await engine.safe_run(app_id)
        
        # Thinking and Self-Fixing phase
        if result == "RETRY":
            update_msg = f"🔧 **Self-Fix Triggered!**\n> Error: `{engine.last_error[:50]}...`\n> Action: `Wiping cache & Rebooting Engine`\n> Retrying for {ctx.author.mention}..."
            await ctx.send(update_msg, delete_after=10)
            result = await engine.safe_run(app_id)

    if result and result != "RETRY" and os.path.exists(result):
        # Direct File or Cloud Fallback
        size = os.path.getsize(result)
        if size > 24 * 1024 * 1024:
            await msg.edit(content="☁️ Too big for Discord. Uploading to Cloud...")
            url = await asyncio.to_thread(upload_to_cloud, result)
            await ctx.send(f"🔔 {ctx.author.mention} **Download Link Ready!**\n🔗 {url}")
            await msg.delete()
        else:
            await ctx.send(content=f"✅ {ctx.author.mention} **Fixed & Ready!**", file=discord.File(result))
            await msg.delete()
        os.remove(result)
    else:
        await msg.edit(content=f"❌ {ctx.author.mention}, the site failed to respond even after a self-fix.")

def get_steam_id(query):
    try:
        r = requests.get(f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US", timeout=5)
        return str(r.json()['items'][0]['id']) if r.json()['items'] else None
    except: return None

def upload_to_cloud(file_path):
    try:
        r = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": open(file_path, "rb")}, timeout=60)
        return r.text if r.status_code == 200 else None
    except: return None

@bot.event
async def on_ready():
    global engine
    engine = AutonomousEngine()
    print(f"🔥 Self-Healing Bot Online: {bot.user}")

if __name__ == "__main__":
    while True:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"System Crash: {e}. Rebooting...")
            time.sleep(5)
