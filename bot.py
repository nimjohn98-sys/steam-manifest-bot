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

def get_game_name(appid):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        r = requests.get(url).json()
        if r and r.get(str(appid), {}).get('success'):
            return r[str(appid)]['data']['name']
    except:
        return "Steam_Game"
    return "Steam_Game"

@bot.event
async def on_ready():
    print(f'🚀 Bot Online: {bot.user}')

@bot.command()
@commands.cooldown(4, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    """Generates the FULL ZIP for Steam Tools."""
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Use a numeric AppID.")

    async with ctx.typing():
        name = get_game_name(appid)
        
        # 1. The .acf file (This makes it show up in the Library)
        acf_content = f""" "AppState"
{{
    "appid" "{appid}"
    "Universe" "1"
    "name" "{name}"
    "StateFlags" "4"
    "installdir" "{name}"
}}
"""
        # 2. The .lua file (This makes the 'Play' button work in Steam Tools)
        lua_content = f'add_app({appid}, "{name}")'

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"appmanifest_{appid}.acf", acf_content)
            zf.writestr(f"{appid}.lua", lua_content)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"SteamTools_Full_{appid}.zip")
        
        embed = discord.Embed(title=f"📦 Full Files for {name}", color=0x00ffff)
        embed.add_field(name="1. The .acf File", value="Put in `Steam/steamapps/`", inline=False)
        embed.add_field(name="2. The .lua File", value="Put in your Tool's `scripts/` or `mani/` folder", inline=False)
        embed.set_footer(text="⚠️ NEVER put the .lua file in the steamapps folder!")
        
        await ctx.send(embed=embed, file=file)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Limit: 4 games per day. Try again later.")

bot.run(TOKEN)
