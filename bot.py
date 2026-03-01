import discord
from discord.ext import commands
import zipfile
import io
import requests

# --- CONFIG ---
# 1. Reset your token in the Discord Dev Portal and paste it here
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg' 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_game_name(appid):
    """Fetches the official game name from Steam for the folder path."""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        response = requests.get(url).json()
        if response and response.get(str(appid), {}).get('success'):
            return response[str(appid)]['data']['name']
    except:
        return "Unknown_Game"
    return "Unknown_Game"

@bot.event
async def on_ready():
    print(f'🚀 Safe Manifest Bot is online as {bot.user}')
    print('Commands: !search <name> | !gen <appid>')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Daily limit reached. Try again in {int(error.retry_after // 3600)} hours.")
    elif isinstance(error, commands.CommandNotFound):
        pass 
    else:
        print(f"Error: {error}")

@bot.command()
async def search(ctx, *, game_name: str):
    """Finds the AppID for a game."""
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    async with ctx.typing():
        try:
            r = requests.get(search_url).json()
            if r.get('total') > 0:
                item = r['items'][0]
                await ctx.send(f"🔍 **Top Result:** {item['name']} | **AppID:** `{item['id']}`\nUse `!gen {item['id']}` to get the file.")
            else:
                await ctx.send("❌ No games found.")
        except:
            await ctx.send("⚠️ Steam search is currently down.")

@bot.command()
@commands.cooldown(4, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    """Generates a SAFE .acf file inside a ZIP."""
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Please provide a numeric AppID.")

    async with ctx.typing():
        game_name = get_game_name(appid)
        
        # This is the EXACT format Steam uses for its own files
        # StateFlags "4" tells Steam the game is installed and updated
        acf_content = f""" "AppState"
{{
    "appid" "{appid}"
    "Universe" "1"
    "name" "{game_name}"
    "StateFlags" "4"
    "installdir" "{game_name}"
    "LastOwner" "0"
}}
"""
        # Package into a ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"appmanifest_{appid}.acf", acf_content)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"Manifest_{appid}.zip")
        
        embed = discord.Embed(title="✅ Safe Manifest Generated", color=0x2ecc71)
        embed.add_field(name="Game", value=game_name, inline=False)
        embed.add_field(name="Install Path", value=f"`Steam/steamapps/appmanifest_{appid}.acf`", inline=False)
        embed.set_footer(text="⚠️ IMPORTANT: Close Steam fully before moving this file!")
        
        await ctx.send(embed=embed, file=file)

bot.run(TOKEN)
