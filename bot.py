import discord
from discord.ext import commands
import requests
import io
import urllib.parse

# 1. IMPORTANT: RESET YOUR TOKEN in the Discord Developer Portal
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# Headers to bypass bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://manifest.youngzm.com/"
}

@bot.event
async def on_ready():
    print(f'✅ Bot Online: {bot.user.name}')
    print('--- KILL ALL OTHER PYTHON INSTANCES TO STOP TRIPLE RESPONSES ---')

@bot.command()
async def snap(ctx, app_id: str):
    """Takes a screenshot using an external API to avoid Chromium errors."""
    await ctx.send(f"📸 Generating screenshot for `{app_id}`...")

    # We use thum.io to take the picture so you don't need Chromium installed
    target_site = f"https://manifest.youngzm.com/?search={app_id}"
    encoded_url = urllib.parse.quote(target_site)
    snap_url = f"https://image.thum.io/get/width/1200/crop/800/wait/3000/{target_site}"

    try:
        response = requests.get(snap_url, stream=True, timeout=20)
        if response.status_code == 200:
            data = io.BytesIO(response.content)
            await ctx.send(file=discord.File(data, filename="screenshot.png"))
        else:
            await ctx.send("❌ Screenshot service failed. The site might be blocking it.")
    except Exception as e:
        await ctx.send(f"⚠️ Snap Error: `{e}`")

@bot.command()
async def gen(ctx, app_id: str):
    """The main command to download the manifest."""
    if ctx.author.bot: return
    msg = await ctx.send(f"🛰️ Accessing database for `{app_id}`...")

    try:
        # Search the API
        search_url = "https://manifest.youngzm.com/api/v3/search"
        r = requests.post(search_url, json={"keyword": app_id}, headers=HEADERS, timeout=10)
        
        # This handles the 'line 1 column 1' error by checking if response is actually JSON
        if "application/json" not in r.headers.get("Content-Type", ""):
            return await msg.edit(content="⚠️ Error: The website sent back a webpage instead of data. They might be blocking the bot.")

        data = r.json()
        items = data.get('data', {}).get('items', [])
        
        # Filter for the ZIP file
        target = next((i for i in items if i.get('name', '').endswith('.zip')), None)
        
        if not target:
            return await msg.edit(content=f"❌ No ZIP file found for `{app_id}`. Use `!snap {app_id}` to check the site.")

        # Download the file
        file_id = target.get('id')
        dl_url = f"https://manifest.youngzm.com/api/v3/file/download/{file_id}"
        file_data = requests.get(dl_url, headers=HEADERS, timeout=30).content
        
        # Send to Discord
        await msg.edit(content=f"✅ File found: `{target.get('name')}`")
        await ctx.send(file=discord.File(io.BytesIO(file_data), filename=target.get('name')))

    except Exception as e:
        await msg.edit(content=f"⚠️ Critical Error: `{str(e)}`")

bot.run(TOKEN)
