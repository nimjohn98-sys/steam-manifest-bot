import discord
from discord.ext import commands
import requests
import io
import os
import cloudscraper

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load secrets from your environment (DO NOT PASTE TOKENS HERE)
DISCORD_TOKEN = os.getenv("MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg")
GITHUB_TOKEN = os.getenv("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")
RAW_LOGIC_URL = "https://raw.githubusercontent.com/nimjohn98-sys/steam-manifest-bot/main/scraper_logic.py"

# --- Placeholder Logic (Will be updated by !update) ---
def download_manifest(app_id):
    raise Exception("Logic not loaded. Please run !update first.")

@bot.event
async def on_ready():
    print(f"✅ Bot is running as {bot.user}")

@bot.command()
async def gen(ctx, app_id: str):
    await ctx.send(f"🧠 **Analyzing security...** Attempting extraction for `{app_id}`")
    
    try:
        # Try to get the file using the logic pulled from GitHub
        data = download_manifest(app_id)
        file_data = io.BytesIO(data)
        await ctx.send(content="✅ **Extraction Successful!**", file=discord.File(file_data, filename=f"{app_id}.zip"))
    
    except Exception as e:
        # Self-Thinking: If it fails, analyze the error
        error_msg = str(e)
        if "403" in error_msg:
            hint = "Website is blocking the bot's 'User-Agent'. Update headers on GitHub."
        elif "404" in error_msg:
            hint = "AppID not found or API path changed. Check the URL on GitHub."
        else:
            hint = "Unknown error. Check the diagnostic log below."
            
        await ctx.send(f"❌ **Failed.**\n**Diagnostic:** `{error_msg}`\n**Hint:** {hint}\n\n*Fix the code on GitHub and run `!update`.*")

@bot.command()
async def update(ctx):
    """Pulls the latest scraper_logic.py from your private GitHub"""
    await ctx.send("🔄 Syncing with GitHub...")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.raw"}
    
    try:
        r = requests.get(RAW_LOGIC_URL, headers=headers)
        if r.status_code == 200:
            exec(r.text, globals())
            await ctx.send("✅ **Update Success!** New logic is now active in memory.")
        else:
            await ctx.send(f"❌ GitHub unreachable. Status: {r.status_code}")
    except Exception as e:
        await ctx.send(f"🚨 Update error: {e}")

bot.run(DISCORD_TOKEN)