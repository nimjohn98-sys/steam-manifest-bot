import discord
from discord.ext import commands
import zipfile
import io
import requests

# --- CONFIG ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_steam_data(appid):
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

# --- ERROR HANDLER ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        # Convert seconds to hours/minutes for the user
        remaining = error.retry_after
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await ctx.send(f"⏳ **Daily Limit Reached!** You can generate more files in **{hours}h {minutes}m**.")
    else:
        raise error

@bot.command()
# 4 uses, per 86400 seconds (24 hours), per user
@commands.cooldown(4, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    """Generates the .lua and .manifest files for SteamTools."""
    if not appid.isdigit():
        await ctx.send("❌ Please enter a valid AppID.")
        # Reset the cooldown since the command failed
        ctx.command.reset_cooldown(ctx)
        return

    async with ctx.typing():
        game_name = get_steam_data(appid)
        
        lua_content = f'-- Generated for SteamTools\nadd_app({appid}, "{game_name}")\n'
        manifest_content = f'{{\n    "appmanifest": {{\n        "appid": "{appid}",\n        "name": "{game_name}",\n        "installdir": "{game_name}",\n        "StateFlags": "4"\n    }}\n}}'

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            zip_file.writestr(f"{appid}.lua", lua_content)
            zip_file.writestr(f"{appid}.manifest", manifest_content)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"SteamTools_{appid}.zip")
        
        await ctx.send(f"🛠️ **SteamTools Files for {game_name}** (AppID: {appid})", file=file)

bot.run(TOKEN)
