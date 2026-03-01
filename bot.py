import discord
from discord.ext import commands
import requests
import io

TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def gen(ctx, app_id: str):
    msg = await ctx.send(f"Searching for App ID `{app_id}`...")

    # The website uses an internal API to list files. 
    # We send a request to the search endpoint directly.
    search_url = "https://manifest.youngzm.com/api/v3/search"
    payload = {"keyword": app_id}
    
    try:
        # 1. Ask the website where the file is
        search_response = requests.post(search_url, json=payload, timeout=10)
        search_data = search_response.json()

        # 2. Look through the results for a ZIP file matching the App ID
        items = search_data.get('data', {}).get('items', [])
        target_file = None
        
        for item in items:
            if app_id in item.get('name', '') and item.get('name', '').endswith('.zip'):
                target_file = item
                break
        
        if target_file:
            # 3. Construct the direct download link
            # Most of these sites use the file ID to generate a download path
            file_id = target_file.get('id')
            download_url = f"https://manifest.youngzm.com/api/v3/file/download/{file_id}"
            
            # 4. Download the actual file
            file_content = requests.get(download_url, timeout=20).content
            
            data = io.BytesIO(file_content)
            discord_file = discord.File(data, filename=f"{app_id}.zip")
            await msg.edit(content=f"✅ Found it! Here is the manifest for `{app_id}`:")
            await ctx.send(file=discord_file)
        else:
            await msg.edit(content=f"❌ Could not find a zip file for App ID `{app_id}` on the site.")

    except Exception as e:
        await msg.edit(content=f"⚠️ Connection Error: The website might be blocking automated requests. Error: {e}")

bot.run(TOKEN)
