import discord
from discord.ext import commands
import requests
import io

# Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot started as {bot.user}")

@bot.command()
async def gen(ctx, app_id: str):
    await ctx.send(f"🛰️ Requesting manifest for `{app_id}`...")

    # The actual API endpoint the download button uses
    url = f"https://manifest.youngzm.com/api/download/{app_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://manifest.youngzm.com/",
        "Accept": "application/zip"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)

        # 1. Check if the site even responded correctly
        if response.status_code != 200:
            await ctx.send(f"❌ Site error: Received status `{response.status_code}`. The file might not exist.")
            return

        # 2. Check if the file is a REAL ZIP (Must start with 'PK')
        if not response.content.startswith(b'PK'):
            await ctx.send("❌ The site sent a response, but it is NOT a valid ZIP. It is likely an HTML error page or a bot-protection screen.")
            return

        # 3. Send the valid file
        file_data = io.BytesIO(response.content)
        await ctx.send(
            content=f"📦 **Manifest Found!** (AppID: {app_id})",
            file=discord.File(file_data, filename=f"{app_id}.zip")
        )

    except Exception as e:
        await ctx.send(f"🚨 Connection error: {str(e)}")

# Your provided token
bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
