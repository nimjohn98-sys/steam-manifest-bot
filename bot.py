import discord
from discord.ext import commands
import requests
import cloudscraper
import io
import os
import base64
from github import Github  # pip install PyGithub
from googlesearch import search  # pip install googlesearch-python

# --- CONFIGURATION ---
DISCORD_TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
GITHUB_TOKEN = "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"
REPO_NAME = "nimjohn98-sys/steam-manifest-bot"
LOGIC_FILE_PATH = "scraper_logic.py"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- GITHUB EDITING LOGIC ---
def update_github_code(new_code):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(LOGIC_FILE_PATH, ref="main")
    repo.update_file(contents.path, "Automated self-healing fix", new_code, contents.sha, branch="main")

# --- SELF-HEALING DIAGNOSTIC ---
async def search_for_fix(error_msg):
    query = f"python cloudscraper {error_msg} fix"
    results = []
    for j in search(query, num=3, stop=3, pause=2):
        results.append(j)
    return results

# Placeholder for the function that will be updated
def download_manifest(app_id):
    raise Exception("Initial logic not loaded. Use !update.")

@bot.command()
async def gen(ctx, app_id: str):
    await ctx.send(f"🧠 **Analyzing AppID `{app_id}`...**")
    try:
        data = download_manifest(app_id)
        await ctx.send(file=discord.File(io.BytesIO(data), filename=f"{app_id}.zip"))
    except Exception as e:
        error_str = str(e)
        await ctx.send(f"🚨 **Error Detected:** `{error_str}`\n🔍 Searching for a solution...")
        
        # Search the web for the error
        links = await search_for_fix(error_str)
        links_str = "\n".join(links)
        
        await ctx.send(f"💡 **I found these potential fixes:**\n{links_str}\n\n**Attempting to self-heal code...**")
        
        # Example: If the error is a specific 403, we auto-update the User-Agent
        if "403" in error_str:
            new_logic = f"""
import cloudscraper
def download_manifest(app_id):
    scraper = cloudscraper.create_scraper(browser={{'browser': 'chrome', 'platform': 'windows'}})
    url = f"https://manifest.youngzm.com/api/download/{{app_id}}"
    r = scraper.get(url)
    return r.content
"""
            try:
                update_github_code(new_logic)
                await ctx.send("✅ **GitHub updated!** Run `!update` to apply the fix.")
            except Exception as ge:
                await ctx.send(f"❌ Failed to edit GitHub: {ge}")

@bot.command()
async def update(ctx):
    await ctx.send("🔄 Syncing brain with GitHub...")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.raw"}
    r = requests.get(f"https://raw.githubusercontent.com/{REPO_NAME}/main/{LOGIC_FILE_PATH}", headers=headers)
    if r.status_code == 200:
        exec(r.text, globals())
        await ctx.send("✅ **New logic applied!**")

bot.run(DISCORD_TOKEN)
