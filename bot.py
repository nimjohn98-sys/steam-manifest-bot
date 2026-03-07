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
    print(f'🚀 ACF Native Bot Online: {bot.user}')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📦 Steam ACF Generator", color=0x1f618d)
    embed.add_field(name="Commands", value="`!search [game]`\n`!gen [appid]`", inline=False)
    embed.add_field(name="How to use", value="1. Close Steam.\n2. Open ZIP.\n3. Drag the **steamapps** folder into your main Steam folder.\n4. Open Steam.", inline=False)
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
        await ctx.send("⚠️ Steam API busy.")

@bot.command()
@commands.cooldown(5, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Enter a numeric ID.")

    async with ctx.typing():
        try:
            name = get_game_name(appid)
            
            # This is the NATIVE Steam AppManifest format
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
            # ZIP with folder structure for ZERO WORK drag-and-drop
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                # We put the .acf inside 'steamapps' so you just drag the folder
                zf.writestr(f"steamapps/appmanifest_{appid}.acf", acf_content)
            
            zip_buffer.seek(0)
            file = discord.File(fp=zip_buffer, filename=f"Native_ACF_{appid}.zip")
            
            await ctx.send(f"✅ **{name}** (ACF format). Drag 'steamapps' to your Steam folder.", file=file)
            
        except Exception as e:
            await ctx.send(f"⚠️ Error creating file: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Daily limit reached (5/5). Try again in {int(error.retry_after // 3600)}h.")

bot.run(TOKEN)
