import discord
from discord.ext import commands
import zipfile
import io
import requests
import urllib.parse

# --- CONFIGURATION ---
# 1. Reset your token in the Dev Portal and paste it here
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# 2. This prefix must be used in Discord (e.g., !search or !gen)
COMMAND_PREFIX = '!' 

intents = discord.Intents.default()
intents.message_content = True  # CRITICAL: Must be enabled in Dev Portal too
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

def get_game_name(appid):
    """Fetches the official game name for the installdir."""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        response = requests.get(url).json()
        if response and response.get(str(appid), {}).get('success'):
            return response[str(appid)]['data']['name']
    except Exception as e:
        print(f"Name lookup error: {e}")
    return "Steam Game"

def generate_acf(appid, name):
    """Creates the text content of the appmanifest file."""
    return f""" "AppState"
{{
    "appid" "{appid}"
    "Universe" "1"
    "name" "{name}"
    "StateFlags" "4"
    "installdir" "{name}"
    "LastUpdated" "0"
    "UpdateResult" "0"
    "SizeOnDisk" "0"
    "buildid" "0"
    "LastOwner" "0"
    "BytesToDownload" "0"
    "BytesDownloaded" "0"
    "AutoUpdateBehavior" "0"
    "AllowOtherDownloadsWhileRunning" "0"
    "ScheduledAutoUpdate" "0"
    "InstalledDepots"
    {{
    }}
}}
"""

@bot.event
async def on_ready():
    print(f'🚀 Bot is logged in as: {bot.user.name}')
    print(f'🤖 Message Content Intent: {bot.intents.message_content}')
    print('--- Bot is ready for commands ---')

@bot.event
async def on_command_error(ctx, error):
    """Prints errors to the console so you can see why a command failed."""
    print(f"❌ Error detected: {error}")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Missing info. Usage: `!gen <appid>` or `!search <name>`")
    else:
        await ctx.send(f"⚠️ An error occurred: {error}")

@bot.command()
async def search(ctx, *, game_name: str):
    """Finds a game's AppID. Usage: !search Terraria"""
    print(f"🔍 Searching for: {game_name}")
    search_url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(game_name)}&l=english&cc=US"
    
    async with ctx.typing():
        try:
            r = requests.get(search_url).json()
            if r.get('total', 0) > 0:
                top_result = r['items'][0]
                name = top_result['name']
                appid = top_result['id']
                
                embed = discord.Embed(title="🔍 Steam Search Results", color=0x3498db)
                embed.add_field(name="Top Match", value=name, inline=True)
                embed.add_field(name="AppID", value=f"`{appid}`", inline=True)
                embed.set_footer(text=f"Type '!gen {appid}' to get the manifest.")
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ No games found. Try a different name.")
        except Exception as e:
            await ctx.send("⚠️ Failed to connect to Steam Search.")
            print(e)

@bot.command()
async def gen(ctx, appid: str):
    """Generates a ZIP with the .acf file. Usage: !gen 105600"""
    if not appid.isdigit():
        await ctx.send("❌ Please provide a numeric AppID (e.g., `!gen 105600`).")
        return

    print(f"📦 Generating manifest for ID: {appid}")
    async with ctx.typing():
        game_name = get_game_name(appid)
        manifest_content = generate_acf(appid, game_name)
        
        # Build ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(f"appmanifest_{appid}.acf", manifest_content)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"manifest_{appid}.zip")
        
        await ctx.send(f"✅ **Manifest for {game_name}** is ready!", file=file)

bot.run(TOKEN)
