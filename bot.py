import os, discord, asyncio, glob, shutil, time, requests, sys
from discord.ext import commands
from DrissionPage import ChromiumPage, ChromiumOptions
from github import Github # Run: pip install PyGithub

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
# YOUR GITHUB TOKEN - I've added it here as requested
GITHUB_TOKEN = "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" 
REPO_NAME = "https://github.com/nimjohn98-sys/steam-manifest-bot/edit/main/bot.py" # <--- MAKE SURE THIS IS CORRECT
TARGET_SITE = "https://manifest.youngzm.com/"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- ENGINE ---
class AutonomousEngine:
    def __init__(self):
        self.browser = None
        self.lock = asyncio.Lock()
        self.last_error = "None"
        self.start_engine()

    def start_engine(self):
        try:
            if sys.platform == "win32":
                os.system("taskkill /f /im chrome.exe /t >nul 2>&1")
            
            co = ChromiumOptions()
            co.headless(True)
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-gpu')
            
            self.browser = ChromiumPage(co)
            self.browser.get(TARGET_SITE)
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    async def self_fix_github(self, error_msg):
        """Logic to overwrite its own code on GitHub when a crash happens"""
        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            contents = repo.get_contents("main.py") 
            current_code = contents.decoded_content.decode()
            
            # Example fix logic: if browser locks up, add a force-restart line
            if "NoneType" in error_msg:
                new_code = current_code.replace("self.browser.set", "if not self.browser: self.start_engine()\n            self.browser.set")
                repo.update_file(contents.path, "🤖 Self-Fix: Resolving Browser Lock", new_code, contents.sha)
                return True
        except Exception as e:
            print(f"GitHub Update Failed: {e}")
        return False

    async def safe_run(self, app_id):
        try:
            if not self.browser: self.start_engine()
            
            job_id = int(time.time())
            work_dir = os.path.abspath(f"win_job_{app_id}_{job_id}")
            os.makedirs(work_dir, exist_ok=True)
            
            self.browser.set.download_path(work_dir)
            self.browser.run_js(f'document.getElementById("appId").value = "{app_id}";')
            self.browser.run_js('downloadManifest();')

            for _ in range(120):
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
            self.start_engine()
            return "RETRY"
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

engine = None

@bot.command(name='gen')
async def gen(ctx, *, query: str = None):
    if not query: return await ctx.send(f"❓ {ctx.author.mention}, need a game name.")
    
    app_id = await asyncio.to_thread(get_steam_id, query)
    msg = await ctx.send(f"⚡ {ctx.author.mention}, processing `{app_id}`...")

    async with engine.lock:
        result = await engine.safe_run(app_id)
        
        if result == "RETRY":
            await ctx.send("🔧 **Local Fix Attempted...**", delete_after=5)
            result = await engine.safe_run(app_id)
            
            if result == "RETRY":
                await ctx.send("🧠 **Fixing my own code on GitHub to prevent this from happening again...**")
                if await engine.self_fix_github(engine.last_error):
                    await ctx.send("✅ **Code Fixed!** Restarting...")
                    sys.exit()

    if result and result != "RETRY" and os.path.exists(result):
        await ctx.send(content=f"✅ {ctx.author.mention} **Fixed & Ready!**", file=discord.File(result))
        await msg.delete()
        os.remove(result)

def get_steam_id(query):
    try:
        r = requests.get(f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US", timeout=5)
        return str(r.json()['items'][0]['id']) if r.json()['items'] else None
    except: return None

@bot.event
async def on_ready():
    global engine
    engine = AutonomousEngine()
    print(f"🔥 Self-Updating Bot Online: {bot.user}")

if __name__ == "__main__":
    bot.run(TOKEN)
