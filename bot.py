import discord
from discord.ext import commands
import zipfile
import io
import requests

# --- CONFIG ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# Standard intents
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
    # Only print this once to confirm 1 instance is running
    print(f'🚀 Bot Online: {bot.user} (ID: {bot.user.id})')

# --- PREVENT DUPLICATES ---
@bot.event
async def on_message(message):
    # If you have an on_message event, you MUST include this line 
    # or commands will trigger twice or not at all.
    if message.author == bot.user:
        return
    await bot.process_commands(message)

# --- ERROR HANDLER ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        remaining = error.retry_after
        await ctx.send(f"⏳ **Limit Reached!** Try again in {int(remaining//3600)}h {int((remaining%3600)//60)}m.", delete_after=10)
    elif isinstance(error, commands.CommandNotFound):
        pass # Ignore unknown commands to keep chat clean
    else:
        print(f"Error: {error}")

# --- THE COMMAND ---
@bot.command()
@commands.cooldown(4, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    """Generates the .lua and .manifest files for SteamTools."""
    if not appid.isdigit():
        await ctx.send("❌ Valid AppID required.", delete_after=5)
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
        
        # Only sends once
        await ctx.send(f"🛠️ **SteamTools Files for {game_name}**", file=file)

bot.run(TOKEN)
