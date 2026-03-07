import discord
from discord.ext import commands
import zipfile
import io
import requests
import urllib.parse

# --- CONFIG ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg' 

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
    print(f'🚀 ACF + Manifest Bot Online: {bot.user}')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📦 Steam All-In-One Generator", color=0x27ae60)
    embed.add_field(name="Commands", value="`!search [game]`\n`!gen [appid]`", inline=False)
    embed.add_field(name="Zero-Work Instructions", value="1. Close Steam.\n2. Open ZIP.\n3. Drag **steamapps** and **manifests** folders into your main Steam/Tool folder.\n4. Merge folders and restart Steam.", inline=False)
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
            await ctx.send("❌ No game found.")
    except:
        await ctx.send("⚠️ Steam API error.")

@bot.command()
@commands.cooldown(5, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Enter a numeric ID.")

    async with ctx.typing():
        try:
            name = get_game_name(appid)
            
            # 1. Native Steam ACF Content
            acf_content = f""" "AppState"
{{
    "appid" "{appid}"
    "Universe" "1"
    "name" "{name}"
    "StateFlags" "4"
    "installdir" "{name}"
    "LastOwner" "0"
}}
"""
            # 2. SteamTools Manifest Content (JSON)
            manifest_content = f"""{{
    "appmanifest": {{
        "appid": "{appid}",
        "name": "{name}",
        "StateFlags": "4"
    }}
}}"""

            # ZIP with folder structure for ZERO WORK
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                # The ACF goes in steamapps
                zf.writestr(f"steamapps/appmanifest_{appid}.acf", acf_content)
                # The Manifest goes in manifests (for SteamTools/GreenLuma)
                zf.writestr(f"manifests/{appid}.manifest", manifest_content)
            
            zip_buffer.seek(0)
            file = discord.File(fp=zip_buffer, filename=f"Full_Pack_{appid}.zip")
            
            await ctx.send(f"✅ **{name}** Pack Ready! (5 daily limit)", file=file)
            
        except Exception as e:
            await ctx.send(f"⚠️ Error: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Daily limit reached. Try again in {int(error.retry_after // 3600)}h.")

bot.run(TOKEN)
