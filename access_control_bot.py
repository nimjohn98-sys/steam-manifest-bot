import discord
from discord.ext import commands
import zipfile
import io
import requests

# --- CONFIG ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
TARGET_CHANNEL_NAME = "🗣️║manifest"
REQUIRED_ROLE = "Level 15+"
INFINITE_ROLES = ["Owner", "Founder", "Admin"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

def get_game_name(appid):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic"
        r = requests.get(url, timeout=5).json()
        if r and r.get(str(appid), {}).get('success'):
            return r[str(appid)]['data']['name']
    except:
        pass
    return "Steam_Game"

def has_permission():
    async def predicate(ctx):
        user_roles = [role.name for role in ctx.author.roles]
        is_staff = any(r in user_roles for r in INFINITE_ROLES)
        if ctx.channel.name != TARGET_CHANNEL_NAME and not is_staff:
            return False
        if REQUIRED_ROLE in user_roles or is_staff:
            return True
        await ctx.send(f"⚠️ Access Denied: Requires `{REQUIRED_ROLE}`.")
        return False
    return commands.check(predicate)

@bot.command()
@has_permission()
@commands.cooldown(20, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    async with ctx.typing():
        name = get_game_name(appid)
        
        # Enhanced ACF to force "Play" button
        acf = f""" "AppState"
{{
    "appid" "{appid}"
    "Universe" "1"
    "name" "{name}"
    "StateFlags" "4"
    "installdir" "{name}"
    "LastOwner" "0"
    "AutoUpdateBehavior" "0"
    "AllowOtherDownloadsWhileRunning" "0"
}}"""

        manifest = f'{{"appmanifest":{{"appid":"{appid}","name":"{name}","StateFlags":"4"}}}}'

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"steamapps/appmanifest_{appid}.acf", acf)
            zf.writestr(f"manifests/{appid}.manifest", manifest)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"Fix_Purchase_{appid}.zip")
        await ctx.send(f"✅ **{name}** fix ready! Close Steam completely before dragging.", file=file)

bot.run(TOKEN)
