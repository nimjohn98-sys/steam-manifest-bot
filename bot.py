import discord
from discord.ext import commands
import requests
import cloudscraper
import io
import os
import traceback

# --- 1. HARDCODED TOKENS ---
DISCORD_TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
GITHUB_TOKEN = "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"
LOGIC_URL = "https://raw.githubusercontent.com/nimjohn98-sys/steam-manifest-bot/main/scraper_logic.py"

# --- 2. BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True  # Ensure this is ON in the Discord Dev Portal
bot = commands.Bot(command_prefix="!", intents=intents)

# This function gets replaced by your GitHub code when you type !update
def download_manifest(app_id):
    raise Exception("Bot logic not loaded. Type !update to sync with GitHub.")

@bot.event
async def on_ready():
    print(f"✅ Logged in as: {bot.user}")
    print("🚀 Status: Ready. Remember to run !update if this is a fresh start.")

@bot.command()
async def gen(ctx, app_id: str):
    await ctx.send(f"🧠 **Thinking...** Extraction process started for `{app_id}`")
    
    try:
        # Calls the function we pulled from GitHub
        data = download_manifest(app_id)
        
        if data:
            file_data = io.BytesIO(data)
            await ctx.send(
                content=f"📦 **Success!** Extracted manifest for `{app_id}`.",
                file=discord.File(file_data, filename=f"manifest_{app_id}.zip")
            )
    except Exception as e:
        # Self-Thinking Diagnostic Report
        err = str(e)
        hint = "Check your scraper_logic.py file on GitHub."
        if "403" in err: hint = "The website is blocking our headers. Try changing User-Agent."
        if "404" in err: hint = "The AppID is invalid or the download path changed."
        
        await ctx.send(f"❌ **Extraction Error**\n**Log:** `{err}`\n**Hint:** {hint}")

@bot.command()
async def update(ctx):
    """Downloads the scraper_logic.py file from GitHub and injects it into the bot"""
    await ctx.send("🔄 Pulling latest logic from GitHub repo...")
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    
    try:
        r = requests.get(LOGIC_URL, headers=headers, timeout=15)
        if r.status_code == 200:
            # This 'exec' overwrites the download_manifest function above
            exec(r.text, globals())
            await ctx.send("✅ **Brain Synchronized!** You can now use `!gen`.")
        else:
            await ctx.send(f"❌ GitHub sync failed. Error Code: `{r.status_code}`")
    except Exception as e:
        await ctx.send(f"🚨 **Critical Sync Error:** {e}")

# --- 3. RUN BOT ---
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    print(f"CRITICAL ERROR STARTING BOT: {e}")
