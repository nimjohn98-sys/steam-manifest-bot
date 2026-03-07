import discord
from discord.ext import commands
import zipfile
import io
import requests
import urllib.parse

# --- CONFIG ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# Role Names
INFINITE_ROLES = ["Owner", "Founder", "Admin"]
REQUIRED_ROLE = "Level 15+"  # Only this role and above can use the bot
STANDARD_LIMIT = 20

intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Essential to check user roles
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- ACCESS CHECK ---
def has_permission():
    async def predicate(ctx):
        user_roles = [role.name for role in ctx.author.roles]
        # Allow if they have the Level 15+ role OR are a Founder/Owner
        if REQUIRED_ROLE in user_roles or any(r in user_roles for r in INFINITE_ROLES):
            return True
        await ctx.send(f"⚠️ **Access Denied:** You must be `{REQUIRED_ROLE}` to use the manifest bot.")
        return False
    return commands.check(predicate)

# --- COOLDOWN LOGIC ---
def custom_cooldown(msg):
    if any(role.name in INFINITE_ROLES for role in msg.author.roles):
        return None # No limit for Owners/Founders
    return commands.Cooldown(STANDARD_LIMIT, 86400) # 20 per day for Level 15+

def get_game_name(appid):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic"
        r = requests.get(url, timeout=5).json()
        if r and r.get(str(appid), {}).get('success'):
            return r[str(appid)]['data']['name']
    except:
        pass
    return "Steam_Game"

@bot.event
async def on_ready():
    print(f'🚀 Access-Locked Bot Online: {bot.user}')

@bot.command()
@has_permission()
async def search(ctx, *, query: str):
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
    try:
        r = requests.get(url, timeout=5).json()
        if r.get('items'):
            game = r['items'][0]
            await ctx.send(f"🔍 **Found:** {game['name']} | ID: `{game['id']}`")
        else:
            await ctx.send("❌ No game found.")
    except:
        await ctx.send("⚠️ Steam API error.")

@bot.command()
@has_permission()
@commands.dynamic_cooldown(custom_cooldown, commands.BucketType.user)
async def gen(ctx, appid: str):
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Enter a numeric ID.")

    async with ctx.typing():
        try:
            name = get_game_name(appid)
            
            acf = f' "AppState"\n{{\n    "appid" "{appid}"\n    "name" "{name}"\n    "StateFlags" "4"\n    "installdir" "{name}"\n}}'
            manifest = f'{{"appmanifest":{{"appid":"{appid}","name":"{name}","StateFlags":"4"}}}}'

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                # Same zero-work folder structure
                zf.writestr(f"steamapps/appmanifest_{appid}.acf", acf)
                zf.writestr(f"manifests/{appid}.manifest", manifest)
            
            zip_buffer.seek(0)
            file = discord.File(fp=zip_buffer, filename=f"Pack_{appid}.zip")
            await ctx.send(f"✅ **{name}** Generated for {ctx.author.mention}!", file=file)
            
        except Exception as e:
            await ctx.send(f"⚠️ Error: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ **Limit Reached!** (20/24h). Owners/Founders have no limit.")
    elif isinstance(error, commands.CheckFailure):
        pass # Message already sent in the check
    else:
        print(f"Error: {error}")

bot.run(TOKEN)
