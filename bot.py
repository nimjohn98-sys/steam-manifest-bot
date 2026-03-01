import discord
from discord.ext import commands
import requests
import io

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot is online as {bot.user}')

@bot.command()
async def gen(ctx, app_id: str):
    """Fetches a manifest zip from youngzm.com based on App ID."""
    
    # URL structure for the manifest site
    url = f"https://manifest.youngzm.com/manifest/{app_id}.zip"
    
    await ctx.send(f"📂 Attempting to retrieve manifest for App ID: `{app_id}`...")

    try:
        # Request the file
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            # Convert the byte response into a file-like object
            zip_file = io.BytesIO(response.content)
            
            # Send the file directly to the channel
            discord_file = discord.File(zip_file, filename=f"{app_id}.zip")
            await ctx.send(content=f"✨ Found! Here is the file for `{app_id}`:", file=discord_file)
        
        elif response.status_code == 404:
            await ctx.send(f"❌ Error: App ID `{app_id}` not found on the manifest server.")
        else:
            await ctx.send(f"⚠️ Server returned an error code: {response.status_code}")

    except Exception as e:
        await ctx.send(f"⚙️ An internal error occurred: {e}")

# Your specific token is inserted here
bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
