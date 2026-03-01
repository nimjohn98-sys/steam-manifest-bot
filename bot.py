import discord
from discord.ext import commands
import requests
import io

# 1. REPLACE THIS TOKEN IMMEDIATELY IN THE DEVELOPER PORTAL
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True 

# Set help_command=None to prevent duplicate help triggers
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # This helps you see if multiple versions are running
    print(f'Logged in as: {bot.user.name}')
    print('Stop all other Python windows to prevent triple responses!')

@bot.command()
async def gen(ctx, app_id: str):
    # Prevent the bot from replying to itself or other bots
    if ctx.author.bot:
        return

    await ctx.send(f"🔎 Searching database for App ID: `{app_id}`...")

    # The website's internal search API
    search_url = "https://manifest.youngzm.com/api/v3/search"
    payload = {"keyword": app_id}
    
    try:
        # Step 1: Search for the file ID
        r = requests.post(search_url, json=payload, timeout=10)
        data = r.json()
        
        items = data.get('data', {}).get('items', [])
        
        if not items:
            return await ctx.send(f"❌ No manifest found for `{app_id}`. Try a different ID.")

        # Step 2: Find the exact .zip file in the results
        target_file = None
        for item in items:
            if item.get('name', '').endswith('.zip'):
                target_file = item
                break
        
        if not target_file:
            return await ctx.send(f"❌ Found entries for `{app_id}`, but none are ZIP files.")

        file_id = target_file.get('id')
        file_name = target_file.get('name')

        # Step 3: Get the Direct Download URL
        # We call the download API to get the actual source link
        download_api = f"https://manifest.youngzm.com/api/v3/file/download/{file_id}"
        
        # Download the bits
        file_bytes = requests.get(download_api, timeout=30).content
        
        # Step 4: Send to Discord
        final_file = discord.File(io.BytesIO(file_bytes), filename=file_name)
        await ctx.send(content=f"✅ **Success!** Downloaded: `{file_name}`", file=final_file)

    except Exception as e:
        await ctx.send(f"⚠️ Error: `{str(e)}`")

@bot.command()
async def snap(ctx, app_id: str):
    """Simple screenshot command using an external viewer"""
    url = f"https://image.thum.io/get/width/1200/crop/800/wait/2000/https://manifest.youngzm.com/?search={app_id}"
    await ctx.send(f"📸 Screenshot of search results for `{app_id}`: {url}")

# This check prevents the bot from starting multiple times in one script
if __name__ == "__main__":
    bot.run(TOKEN)
