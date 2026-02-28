import discord
from discord.ext import commands
import requests
import io

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# The target repository
BASE_URL = "https://manifest.youngzm.com/"

@bot.event
async def on_ready():
    print(f'--- Bot is Online ---')
    print(f'Logged in as: {bot.user.name}')

@bot.command()
async def manifest(ctx, app_id: str):
    """Downloads a manifest zip and uploads it to the chat."""
    await ctx.send(f"Searching for AppID `{app_id}` on the manifest repo...")

    # Note: If the website uses a different path like /files/ or /get/, 
    # you may need to update this URL string.
    target_url = f"{BASE_URL}{app_id}.zip"

    try:
        # Stream the file from the website
        response = requests.get(target_url, timeout=15)
        
        if response.status_code == 200:
            # Create a file object in memory
            file_data = io.BytesIO(response.content)
            discord_file = discord.File(file_data, filename=f"{app_id}_manifest.zip")
            
            await ctx.send(content=f"📦 Here is the manifest for **{app_id}**:", file=discord_file)
        elif response.status_code == 404:
            await ctx.send(f"❌ Could not find a zip for AppID `{app_id}`. Are you sure it's on the site?")
        else:
            await ctx.send(f"⚠️ Site returned error code: {response.status_code}")
            
    except Exception as e:
        await ctx.send(f"🚨 Bot Error: {str(e)}")

# Using the token you provided
bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
