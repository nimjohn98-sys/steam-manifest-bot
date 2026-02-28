import discord
from discord.ext import commands
import requests
import io

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://manifest.youngzm.com/"
}

@bot.event
async def on_ready():
    print(f'✅ Bot is live as {bot.user.name}')

# --- ERROR HANDLER ---
@bot.event
async def on_command_error(ctx, error):
    """Handles cooldown errors globally."""
    if isinstance(error, commands.CommandOnCooldown):
        # error.retry_after gives the remaining time in seconds
        msg = f"⏳ **Slow down!** You can use this again in `{error.retry_after:.1f}` seconds."
        await ctx.send(msg)
    else:
        # For other errors, print them to the console so you can see what happened
        print(f"Error: {error}")

# --- COMMANDS ---

@bot.command()
# COOLDOWN: 1 use, every 10 seconds, per User
@commands.cooldown(1, 10, commands.BucketType.user)
async def gen(ctx, app_id: str):
    """Downloads the manifest zip using the site's API endpoint."""
    await ctx.send(f"🛠️ Generating manifest zip for AppID `{app_id}`...")

    api_url = f"https://manifest.youngzm.com/api/download/{app_id}"

    try:
        response = requests.get(api_url, headers=HEADERS, timeout=20)
        
        if response.status_code == 200 and len(response.content) > 1000:
            file_data = io.BytesIO(response.content)
            zip_file = discord.File(file_data, filename=f"{app_id}.zip")
            await ctx.send(content=f"✅ **Done!** Here is your manifest for `{app_id}`:", file=zip_file)
        else:
            await ctx.send(f"❌ **Error:** Valid zip not found for `{app_id}`. It might not be in the database.")
            
    except Exception as e:
        await ctx.send(f"🚨 **Bot Error:** {str(e)}")

@bot.command()
@commands.cooldown(1, 60, commands.BucketType.user) # 5 second cooldown for search
async def appid(ctx, *, game_name: str):
    """Quickly find an AppID via Steam's search API."""
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    try:
        r = requests.get(search_url).json()
        if r.get('total', 0) > 0:
            game = r['items'][0]
            await ctx.send(f"🔍 **Result:** {game['name']} | AppID: `{game['id']}`")
        else:
            await ctx.send(f"🔍 No results found for `{game_name}`.")
    except:
        await ctx.send("🚨 Search timed out.")

# Your Token
bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
