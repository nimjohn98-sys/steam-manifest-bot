import os
import discord
from discord.ext import commands
import asyncio
import time
import re
import subprocess
import random
import shutil
import glob
import requests
from concurrent.futures import ThreadPoolExecutor
from DrissionPage import ChromiumPage, ChromiumOptions

# --- ENCRYPTED CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
executor = ThreadPoolExecutor(max_workers=5)


class SentinelEngine:
    def __init__(self):
        self.page = None

    def hard_reset(self):
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'], capture_output=True)
            shutil.rmtree('temp_profiles', ignore_errors=True)
        except:
            pass

        co = ChromiumOptions()
        co.set_browser_path(CHROME_PATH)
        co.set_local_port(random.randint(10000, 30000))
        co.headless(True)
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-blink-features=AutomationControlled')
        self.page = ChromiumPage(co)

    def universal_id_lookup(self, name):
        if name.isdigit(): return name
        try:
            r = requests.get(f"https://store.steampowered.com/api/storesearch/?term={name}", timeout=5)
            return str(r.json()['items'][0]['id'])
        except:
            try:
                if not self.page: self.hard_reset()
                self.page.get(f"https://steamdb.info/search/?a=app&q={name.replace(' ', '+')}")
                match = re.findall(r'/app/(\d+)', self.page.html)
                return match[0] if match else None
            except:
                return None


engine = SentinelEngine()


def run_apex_logic(query):
    app_id = engine.universal_id_lookup(query)
    if not app_id:
        return {"error": "Identification Failure: AppID not found."}

    if not engine.page: engine.hard_reset()
    work_dir = os.path.join(os.getcwd(), f"zip_job_{app_id}")
    os.makedirs(work_dir, exist_ok=True)
    engine.page.set.download_path(work_dir)
    debug_img = os.path.join(os.getcwd(), f"diag_{app_id}.png")

    try:
        engine.page.get(TARGET_SITE)

        if not engine.page.ele('@id=appId', timeout=15):
            engine.page.get_screenshot(path=debug_img)
            return {"error": "Target Site UI Blocked.", "debug": debug_img}

        # JS Injection to fill ID
        engine.page.run_js(f'document.getElementById("appId").value = "{app_id}";')

        # TRIGGER ZIP GENERATION:
        # We target the site's logic that handles the ZIP packing specifically
        try:
            # Attempt to call the ZIP-specific download if available,
            # otherwise trigger the main download which bundles the ZIP
            engine.page.run_js('downloadManifest();')
        except:
            engine.page.ele('@id=download-btn').click(force=True)

        # EXTENDED POLLING FOR ZIP:
        # ZIP files take longer to generate on the server than single manifests.
        # We increase the timeout to 60 seconds.
        for i in range(60):
            time.sleep(1)
            # We specifically look for .zip files now
            zip_files = [f for f in glob.glob(os.path.join(work_dir, "*.zip")) if not f.endswith('.crdownload')]
            if zip_files:
                latest_zip = max(zip_files, key=os.path.getctime)
                dest = os.path.join(os.getcwd(), f"Full_Manifest_{app_id}.zip")
                shutil.move(latest_zip, dest)
                return {"path": dest, "id": app_id, "type": "ZIP Bundle"}

            # Fallback check: if the site only provides a manifest despite our request
            manifest_files = [f for f in glob.glob(os.path.join(work_dir, "*.manifest")) if
                              not f.endswith('.crdownload')]
            if manifest_files and i > 30:  # Only settle for manifest after 30 seconds of trying for a ZIP
                dest = os.path.join(os.getcwd(), f"Single_{app_id}.manifest")
                shutil.move(max(manifest_files, key=os.path.getctime), dest)
                return {"path": dest, "id": app_id, "type": "Single (ZIP unavailable)"}

        return {"error": "ZIP Generation Timeout. Server might be under heavy load."}

    except Exception as e:
        engine.page.get_screenshot(path=debug_img)
        engine.hard_reset()
        return {"error": str(e), "debug": debug_img}
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


@bot.command(name='gen')
async def generate(ctx, *, query: str = None):
    if not query: return

    status_msg = await ctx.send(f"📦 **Initializing Full ZIP Retrieval** for: `{query}`...")

    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(executor, run_apex_logic, query)

    if "error" in res:
        await status_msg.edit(content=f"🚨 **Extraction Failure:** {res['error']}")
        if "debug" in res:
            await ctx.send(file=discord.File(res['debug']))
            os.remove(res['debug'])
    else:
        await status_msg.edit(content=f"✅ **Package Secured.** [ID: `{res['id']}`]\nFormat: `{res['type']}`")
        await ctx.send(file=discord.File(res['path']))
        os.remove(res['path'])


if __name__ == "__main__":
    bot.run(TOKEN)
