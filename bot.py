import discord
from discord.ext import commands
import zipfile
import io
import requests
import urllib.parse

# --- CONFIG ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# REPLACE THESE WITH YOUR ACTUAL ROLE NAMES OR IDs
INFINITE_ROLES = ["Owner", "Founder", "Admin"]
STANDARD_LIMIT_ROLES = ["Member", "User", "Verified"]
STANDARD_LIMIT = 20

intents = discord.Intents.default()
intents.message_content = True
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

@bot.event
async def on_ready():
    print(f'🚀 Advanced Role-Based Bot Online: {bot.user}')

# --- CUSTOM COOLDOWN LOGIC ---
def custom_cooldown(msg):
    # Check if user has an infinite role
    if any(role.name in INFINITE_ROLES for role in msg.author.roles):
        return None  # No cooldown
    # Otherwise, apply the 20 per day limit
    return commands.Cooldown(STANDARD_LIMIT, 86400)

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📦 Steam All-In-One (Advanced)", color=0x9b59b6)
    embed.add_field(name="Commands", value="`!search [game]`\n`!gen [appid]`", inline=False)
    embed.add_field(name="Limits", value=f"Founders/Owners: **Infinite**\nOthers: **{STANDARD_LIMIT} per day**", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def search(ctx, *, query: str):
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
    try:
        r = requests.get(url, timeout=5).json()
        if r.get('items'):
            game = r['items'][0]
            await ctx.send(f"🔍 **Found:** {game['name']} | ID: `{game['id']}`")
        else:
            await ctx.send("❌ Game not found.")
    except:
        await ctx.send("⚠️ Steam API error.")

@bot.command()
@commands.dynamic_cooldown(custom_cooldown, commands.BucketType.user)
async def gen(ctx, appid: str):
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Enter a numeric ID.")

    async with ctx.typing():
        try:
            name = get_game_name(appid)
            
            # ACF Content
            acf_content = f' "AppState"\n{{\n    "appid" "{appid}"\n    "name" "{name}"\n    "StateFlags" "4"\n    "installdir" "{name}"\n}}'
            
            # Manifest Content
            manifest_content = f'{{"appmanifest":{{"appid":"{appid}","name":"{name}","StateFlags":"4"}}}}'

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.writestr(f"steamapps/appmanifest_{appid}.acf", acf_content)
                zf.writestr(f"manifests/{appid}.manifest", manifest_content)
            
            zip_buffer.seek(0)
            file = discord.File(fp=zip_buffer, filename=f"Full_Pack_{appid}.zip")
            await ctx.send(f"✅ **{name}** Pack Ready!", file=file)
            
        except Exception as e:
            await ctx.send(f"⚠️ Error: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ **Limit Reached!** You have used your {STANDARD_LIMIT} daily generations. Founders/Owners have no limit.")
    else:
        print(f"Error: {error}")

bot.run(TOKEN)
