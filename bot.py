import discord
from discord.ext import commands
import requests
import io

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# Added a User-Agent so the website doesn't block the bot
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

@bot.event
async def on_ready():
    print(f'✅ Bot is ready as {bot.user.name}')

@bot.command()
async def gen(ctx, app_id: str):
    """Downloads the manifest zip with proper headers."""
    await ctx.send(f"🛰️ Fetching manifest for `{app_id}`... please wait.")
    
    # Updated URL structure: many of these sites use a specific path
    # If this specific link still fails, the site may be using dynamic IDs
    target_url = f"https://manifest.youngzm.com/manifest/{app_id}.zip"

    try:
        response = requests.get(target_url, headers=HEADERS, timeout=15)
        
        # Check if the response is actually a ZIP file and not an HTML page
        content_type = response.headers.get('Content-Type', '')
        
        if response.status_code == 200 and "zip" in content_type.lower():
            file_data = io.BytesIO(response.content)
            df = discord.File(file_data, filename=f"manifest_{app_id}.zip")
            await ctx.send(content=f"📦 **Manifest Ready!** AppID: `{app_id}`", file=df)
        else:
            await ctx.send(f"❌ **Error:** The site didn't return a valid ZIP. It might not have the manifest for `{app_id}` or the URL has changed.")
            
    except Exception as e:
        await ctx.send(f"🚨 **Bot Error:** {str(e)}")

@bot.command()
async def appid(ctx, *, game_name: str):
    """Searches Steam for a game's AppID."""
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    try:
        r = requests.get(search_url).json()
        if r.get('total') > 0:
            game = r['items'][0]
            await ctx.send(f"🔍 **{game['name']}** AppID: `{game['id']}`")
        else:
            await ctx.send("🔍 No games found.")
    except:
        await ctx.send("🚨 Search failed.")

bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
