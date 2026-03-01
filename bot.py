import discord
from discord.ext import commands
import zipfile
import io
import requests

# --- CONFIG ---
# Replace this with your NEW token after you reset it!
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_game_name(appid):
    """Fetches the official game name from Steam API for the folder path."""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        response = requests.get(url).json()
        if response[str(appid)]['success']:
            return response[str(appid)]['data']['name']
    except:
        return "Steam Game"
    return "Steam Game"

def generate_acf(appid, name):
    """Formats the .acf manifest content."""
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
    print(f'🚀 Manifest Bot is online as {bot.user}')

@bot.command()
async def gen(ctx, appid: str):
    """Usage: !gen 105600"""
    if not appid.isdigit():
        await ctx.send("❌ Error: Please provide a numeric AppID.")
        return

    await ctx.mention
    async with ctx.typing():
        game_name = get_game_name(appid)
        manifest_content = generate_acf(appid, game_name)
        
        # Prepare the ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(f"appmanifest_{appid}.acf", manifest_content)
        
        zip_buffer.seek(0)
        
        # Send to user
        file = discord.File(fp=zip_buffer, filename=f"Terraria_Manifest_{appid}.zip")
        embed = discord.Embed(
            title="✅ Manifest Generated",
            description=f"**Game:** {game_name}\n**AppID:** {appid}",
            color=0x2ecc71
        )
        embed.add_field(name="Instructions", value="1. Close Steam.\n2. Drop the .acf into `steamapps/`.\n3. Restart Steam with your Tool.")
        
        await ctx.send(embed=embed, file=file)

bot.run(TOKEN)
