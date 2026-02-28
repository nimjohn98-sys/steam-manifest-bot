import discord
from discord.ext import commands
import requests
import io
import os
from github import Github  # pip install PyGithub
from googlesearch import search  # pip install googlesearch-python

# --- HARDCODED TOKENS ---
DISCORD_TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
GITHUB_TOKEN = "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"
REPO_NAME = "nimjohn98-sys/steam-manifest-bot"
LOGIC_FILE = "scraper_logic.py"
RAW_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{LOGIC_FILE}"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- GITHUB REPAIR ENGINE ---
def repair_code_on_github(error_type):
    """Rewrites scraper_logic.py with a new strategy based on the error."""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(LOGIC_FILE, ref="main")
    
    # Strategy: If it's a 403/HTML block, we rotate the browser signature
    new_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    
    new_content = f"""
import cloudscraper
import requests

def download_manifest(app_id):
    scraper = cloudscraper.create_scraper(browser={{'browser': 'chrome', 'platform': 'windows'}})
    url = f"https://manifest.youngzm.com/api/download/{{app_id}}"
    headers = {{
        "User-Agent": "{new_user_agent}",
        "Referer": "https://manifest.youngzm.com/",
        "Origin": "https://manifest.youngzm.com"
    }}
    r = scraper.get(url, headers=headers, timeout=30)
    
    # Validation: Must start with PK (ZIP header)
    if r.status_code == 200 and r.content.startswith(b'PK'):
        return r.content
    raise Exception(f"Validation Failed: Received {{'HTML' if b'<!DOCTYPE' in r.content else 'Bad Data'}}")
"""
    repo.update_file(contents.path, f"🛠️ Auto-Fix: {error_type}", new_content, contents.sha, branch="main")
    return f"https://github.com/{REPO_NAME}/commit/main"

# Placeholder
def download_manifest(app_id):
    raise Exception("Initial logic missing. Run !update.")

@bot.event
async def on_ready():
    print(f"✅ Steam Tools Bot Online: {bot.user}")

@bot.command()
async def gen(ctx, app_id: str):
    status_msg = await ctx.send(f"🛰️ **Retrieving Manifest:** `{app_id}`...")
    
    try:
        data = download_manifest(app_id)
        # Final check before sending
        if not data.startswith(b'PK'):
            raise Exception("Faulty ZIP detected (HTML or Corrupt Content)")
            
        file_data = io.BytesIO(data)
        await status_msg.edit(content=f"✅ **Success!** Sending real ZIP for `{app_id}`.")
        await ctx.send(file=discord.File(file_data, filename=f"{app_id}.zip"))

    except Exception as e:
        err = str(e)
        await status_msg.edit(content=f"🚨 **Faulty File Detected!**\n**Error:** `{err}`\n🔍 **Searching for fix...**")
        
        # Search for fix links
        search_results = []
        for j in search(f"manifest.youngzm.com {err} fix", num=2, stop=2):
            search_results.append(j)
        
        # NOTIFY: Modifying Code
        await ctx.send(f"🛠️ **Self-Healing Active:** Found possible solutions. Rewriting GitHub code now...")
        try:
            commit_url = repair_code_on_github(err)
            await ctx.send(f"✅ **GitHub Modified!** New logic pushed.\n**Commit:** {commit_url}\n👉 Run `!update` to apply fix.")
        except Exception as ge:
            await ctx.send(f"❌ Failed to rewrite GitHub: `{ge}`")

@bot.command()
async def update(ctx):
    await ctx.send("🔄 **Syncing with GitHub...**")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.raw"}
    r = requests.get(RAW_URL, headers=headers)
    if r.status_code == 200:
        exec(r.text, globals())
        await ctx.send("✅ **Brain Updated.** New scraping logic is live.")

bot.run(DISCORD_TOKEN)