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

# --- SEARCH COMMAND ---
@bot.command()
async def search(ctx, *, game_name: str):
    """Finds the AppID for a game name."""
    search_url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(game_name)}&l=english&cc=US"
    
    async with ctx.typing():
        try:
            r = requests.get(search_url).json()
            if r.get('total') > 0:
                top_result = r['items'][0]
                name = top_result['name']
                appid = top_result['id']
                
                embed = discord.Embed(title="🔍 Steam Search", color=0x3498db)
                embed.add_field(name="Game", value=name, inline=True)
                embed.add_field(name="AppID", value=f"`{appid}`", inline=True)
                embed.set_footer(text=f"Run '!gen {appid}' to get the ZIP.")
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ No games found.")
        except:
            await ctx.send("⚠️ Search is currently unavailable.")

# --- GENERATE COMMAND ---
@bot.command()
@commands.cooldown(4, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    """Generates the website-style ZIP for drag-and-drop."""
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Use a numeric AppID.")

    async with ctx.typing():
        name = get_game_name(appid)
        
        # SteamTools Content
        lua_content = f'add_app({appid}, "{name}")'
        manifest_content = f"""{{
    "appmanifest": {{
        "appid": "{appid}",
        "name": "{name}",
        "StateFlags": "4"
    }}
}}"""

        # Creating ZIP with folder structure for easy drag-and-drop
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"scripts/{appid}.lua", lua_content)
            zf.writestr(f"manifests/{appid}.manifest", manifest_content)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"SteamTools_{appid}.zip")
        
        embed = discord.Embed(title=f"📦 ZIP Ready: {name}", color=0x2ecc71)
        embed.description = "Open the ZIP and drag the **scripts** and **manifests** folders into your SteamTools main folder."
        await ctx.send(embed=embed, file=file)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Limit reached. Try again in {int(error.retry_after // 3600)}h.")

bot.run(TOKEN)
