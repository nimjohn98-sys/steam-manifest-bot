import discord
from discord.ext import commands
import zipfile
import io
import requests

# --- CONFIG ---
TOKEN = 'REPLACE_WITH_YOUR_NEWLY_RESET_TOKEN'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_steam_data(appid):
    """Gets official name and manifest info from Steam."""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        r = requests.get(url).json()
        if r[str(appid)]['success']:
            return r[str(appid)]['data']['name']
    except:
        pass
    return "Unknown Game"

@bot.event
async def on_ready():
    print(f'🚀 SteamTools Bot is online: {bot.user}')

@bot.command()
async def gen(ctx, appid: str):
    """Generates the .lua and .manifest files for SteamTools."""
    if not appid.isdigit():
        await ctx.send("❌ Please enter a valid AppID.")
        return

    async with ctx.typing():
        game_name = get_steam_data(appid)
        
        # 1. Create the ManiLua content
        # This tells SteamTools to add the app to your licensed list
        lua_content = f"""-- Generated for SteamTools
add_app({appid}, "{game_name}")
"""

        # 2. Create the .manifest content
        # This tells SteamTools the game is 'installed'
        manifest_content = f"""{{
    "appmanifest": {{
        "appid": "{appid}",
        "name": "{game_name}",
        "installdir": "{game_name}",
        "StateFlags": "4"
    }}
}}"""

        # 3. Create the ZIP archive
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            # Add files to the ZIP
            zip_file.writestr(f"{appid}.lua", lua_content)
            zip_file.writestr(f"{appid}.manifest", manifest_content)
        
        zip_buffer.seek(0)
        
        # 4. Send to Discord
        file = discord.File(fp=zip_buffer, filename=f"SteamTools_{appid}.zip")
        embed = discord.Embed(title="🛠️ SteamTools Files Ready", color=0x00ffcc)
        embed.add_field(name="Game", value=game_name, inline=True)
        embed.add_field(name="AppID", value=appid, inline=True)
        embed.description = "Download this ZIP and extract the files into your SteamTools **scripts** or **manifests** folder."
        
        await ctx.send(embed=embed, file=file)

bot.run(TOKEN)
