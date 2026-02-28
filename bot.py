import discord
from discord.ext import commands
import requests
import io

# Setup
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

BASE_URL = "https://manifest.youngzm.com/"

@bot.event
async def on_ready():
    print(f'✅ Bot Online: {bot.user.name}')

@bot.command()
async def gen(ctx, app_id: str):
    """Downloads the manifest zip for the given AppID."""
    await ctx.send(f"📂 Attempting to generate/fetch manifest for AppID: `{app_id}`...")
    
    target_url = f"{BASE_URL}{app_id}.zip"
    try:
        response = requests.get(target_url, timeout=15)
        if response.status_code == 200:
            file_data = io.BytesIO(response.content)
            df = discord.File(file_data, filename=f"{app_id}_manifest.zip")
            await ctx.send(content=f"✅ **Success!** Download complete for `{app_id}`:", file=df)
        else:
            await ctx.send(f"❌ **Failed.** The manifest for `{app_id}` isn't available on the server (Error {response.status_code}).")
    except Exception as e:
        await ctx.send(f"🚨 **Error:** {str(e)}")

@bot.command()
async def appid(ctx, *, game_name: str):
    """Searches Steam for a game's AppID."""
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    
    try:
        response = requests.get(search_url).json()
        if response.get('total') > 0:
            # Get the first/top result
            game = response['items'][0]
            name = game['name']
            id = game['id']
            tiny_image = game['tiny_image']
            
            embed = discord.Embed(title="Steam AppID Finder", color=discord.Color.blue())
            embed.add_field(name="Game Name", value=name, inline=True)
            embed.add_field(name="AppID", value=f"`{id}`", inline=True)
            embed.set_thumbnail(url=tiny_image)
            embed.set_footer(text="Use !gen <ID> to try and get the manifest.")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"🔍 No Steam games found matching `{game_name}`.")
    except Exception as e:
        await ctx.send(f"🚨 Search Error: {str(e)}")

# Your Token
bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
