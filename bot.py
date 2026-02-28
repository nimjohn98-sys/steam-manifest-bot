import discord
from discord.ext import commands
import cloudscraper
import io
import requests

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# This is where you would put your RAW GitHub link (click 'Raw' on GitHub to get it)
GITHUB_CODE_URL "https://github.com/nimjohn98-sys/steam-manifest-bot/blob/main/bot.py"

def download_manifest(app_id):
    """Uses cloudscraper to bypass Cloudflare/Bot protection."""
    scraper = cloudscraper.create_scraper()
    url = f"https://manifest.youngzm.com/api/download/{app_id}"
    
    response = scraper.get(url, timeout=30)
    
    if response.status_code == 200 and response.content.startswith(b'PK'):
        return response.content
    return None

@bot.event
async def on_ready():
    print(f"✅ Bot is running as {bot.user}")

@bot.command()
async def gen(ctx, app_id: str):
    await ctx.send(f"🚀 Attempting high-bypass download for `{app_id}`...")
    
    try:
        data = download_manifest(app_id)
        
        if data:
            file_data = io.BytesIO(data)
            await ctx.send(
                content=f"📦 **Manifest Secured!**",
                file=discord.File(file_data, filename=f"{app_id}.zip")
            )
        else:
            await ctx.send("❌ **Bypass Failed.** The site is blocking the current method. Try `!update` to pull a fix from GitHub.")
    
    except Exception as e:
        await ctx.send(f"🚨 Error: {str(e)}")

@bot.command()
async def update(ctx):
    """Fetches new logic from GitHub if the current one is broken."""
    await ctx.send("🔄 Checking GitHub for a logic update...")
    try:
        r = requests.get(GITHUB_CODE_URL)
        if r.status_code == 200:
            # This 'exec' runs the code fetched from GitHub
            # Note: This is powerful but dangerous—only use URLs you control!
            exec(r.text, globals())
            await ctx.send("✅ **Logic Updated!** The bot is now using the latest code from GitHub.")
        else:
            await ctx.send("❌ Could not reach GitHub repository.")
    except Exception as e:
        await ctx.send(f"🚨 Update Failed: {e}")

# Your Token
bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')