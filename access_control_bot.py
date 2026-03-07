import discord
from discord.ext import commands
import zipfile
import io
import requests
import urllib.parse

# --- CONFIGURATION ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# Exact names from your Discord server
TARGET_CHANNEL_NAME = "🗣️║manifest"
REQUIRED_ROLE = "Level 15+"
INFINITE_ROLES = ["Owner", "Founder", "Admin"]
STANDARD_LIMIT = 20

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True  # Required to read !gen
intents.members = True          # Required to check Level 15+ role
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

# --- PERMISSION & CHANNEL CHECK ---
def has_permission():
    async def predicate(ctx):
        user_roles = [role.name for role in ctx.author.roles]
        is_staff = any(r in user_roles for r in INFINITE_ROLES)
        
        # 1. Check Channel (Staff can bypass)
        if ctx.channel.name != TARGET_CHANNEL_NAME and not is_staff:
            return False 

        # 2. Check Role
        if REQUIRED_ROLE in user_roles or is_staff:
            return True
        
        await ctx.send(f"⚠️ **Access Denied:** You must be `{REQUIRED_ROLE}` to use this bot.")
        return False
    return commands.check(predicate)

# --- COOLDOWN LOGIC ---
def custom_cooldown(msg):
    if any(role.name in INFINITE_ROLES for role in msg.author.roles):
        return None # No limit for Owners/Founders
    return commands.Cooldown(STANDARD_LIMIT, 86400) # 20 per 24 hours

@bot.event
async def on_ready():
    print(f'🚀 Bot Online: {bot.user}')
    print(f'🔒 Locked to Channel: {TARGET_CHANNEL_NAME}')
    print(f'🛡️ Required Role: {REQUIRED_ROLE}')

@bot.command()
@has_permission()
async def help(ctx):
    embed = discord.Embed(title="🎮 SteamTools Manifest Bot", color=0x2ecc71)
    embed.add_field(name="`!search [name]`", value="Find a Game's AppID.", inline=False)
    embed.add_field(name="`!gen [appid]`", value="Generate the ZIP pack.", inline=False)
    embed.description = (
        f"**Limits:**\n• {REQUIRED_ROLE}: {STANDARD_LIMIT}/day\n"
        "• Owners/Founders: Infinite\n\n"
        "**Install:** Close Steam -> Open ZIP -> Drag folders to Steam directory."
    )
    await ctx.send(embed=embed)

@bot.command()
@has_permission()
async def search(ctx, *, query: str):
    url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(query)}&l=english&cc=US"
    try:
        r = requests.get(url, timeout=5).json()
        if r.get('items'):
            game = r['items'][0]
            await ctx.send(f"🔍 **Result:** {game['name']} | AppID: `{game['id']}`\nType `!gen {game['id']}` to get files.")
        else:
            await ctx.send("❌ No game found on Steam.")
    except:
        await ctx.send("⚠️ Steam search is lagging. Try again.")

@bot.command()
@has_permission()
@commands.dynamic_cooldown(custom_cooldown, commands.BucketType.user)
async def gen(ctx, appid: str):
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Please provide a numeric AppID.")

    async with ctx.typing():
        try:
            name = get_game_name(appid)
            
            # THE FIX: Forces Steam to see the game as 100% installed
            acf_content = f""" "AppState"
{{
    "appid" "{appid}"
    "Universe" "1"
    "name" "{name}"
    "StateFlags" "4"
    "installdir" "{name}"
    "LastOwner" "0"
    "UpdateResult" "0"
    "BytesToDownload" "0"
    "BytesDownloaded" "0"
    "AutoUpdateBehavior" "0"
}}"""

            manifest_content = f'{{ "appmanifest": {{ "appid": "{appid}", "name": "{name}", "StateFlags": "4" }} }}'

            # Build ZIP with Zero-Work folders
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.writestr(f"steamapps/appmanifest_{appid}.acf", acf_content)
                zf.writestr(f"manifests/{appid}.manifest", manifest_content)
            
            zip_buffer.seek(0)
            file = discord.File(fp=zip_buffer, filename=f"SteamPack_{appid}.zip")
            await ctx.send(f"✅ **{name}** (AppID: {appid})\nDownload and drag the folders into your Steam directory.", file=file)
            
        except Exception as e:
            await ctx.send(f"⚠️ Error generating files: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ **Limit Reached:** You can only generate {STANDARD_LIMIT} games per day.")
    elif isinstance(error, commands.CheckFailure):
        pass # Ignored because has_permission() sends its own message
    else:
        print(f"Error: {error}")

bot.run(TOKEN)
