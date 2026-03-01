import discord
from discord.ext import commands
import zipfile
import io
import requests

# --- CONFIG ---
# If this token stops working, reset it at the Discord Developer Portal.
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg' 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_game_name(appid):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        r = requests.get(url).json()
        if r and r.get(str(appid), {}).get('success'):
            return r[str(appid)]['data']['name']
    except:
        return "Game"
    return "Game"

@bot.event
async def on_ready():
    print(f'🚀 Ultra-Simple Bot Online: {bot.user}')

@bot.command()
@commands.cooldown(4, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    """Generates a ZIP with loose files for the simplest drag-and-drop."""
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Please provide a numeric AppID.")

    async with ctx.typing():
        name = get_game_name(appid)
        
        # 1. Lua File (Works for Watson/GreenLuma)
        lua_content = f'add_app({appid}, "{name}")'
        
        # 2. Manifest File (JSON format for SteamTools)
        manifest_content = f"""{{
    "appmanifest": {{
        "appid": "{appid}",
        "name": "{name}",
        "StateFlags": "4"
    }}
}}"""

        # 3. Create ZIP (No folders, just the files)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"{appid}.lua", lua_content)
            zf.writestr(f"{appid}.manifest", manifest_content)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"SteamTools_{appid}.zip")
        
        await ctx.send(f"✅ **{name}** files ready. Drag these onto your tool!", file=file)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Daily limit reached. You can generate more in {int(error.retry_after // 3600)}h.")

bot.run(TOKEN)
