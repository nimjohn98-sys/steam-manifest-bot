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

def get_game_info(appid):
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
    print(f'🚀 Drag-and-Drop Bot Online: {bot.user}')

@bot.command()
async def search(ctx, *, game_name: str):
    """Finds the AppID easily."""
    search_url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(game_name)}&l=english&cc=US"
    r = requests.get(search_url).json()
    if r.get('total') > 0:
        item = r['items'][0]
        await ctx.send(f"🔍 **Result:** {item['name']} | **AppID:** `{item['id']}`\nUse `!gen {item['id']}`")
    else:
        await ctx.send("❌ No game found.")

@bot.command()
@commands.cooldown(4, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    """Generates the folders for direct drag-and-drop."""
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Enter a number.")

    async with ctx.typing():
        name = get_game_info(appid)
        
        # SteamTools formats
        lua_content = f'add_app({appid}, "{name}")'
        manifest_content = f'{{\n    "appmanifest": {{\n        "appid": "{appid}",\n        "name": "{name}",\n        "StateFlags": "4"\n    }}\n}}'

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            # Matches SteamTools folder structure
            zf.writestr(f"scripts/{appid}.lua", lua_content)
            zf.writestr(f"manifests/{appid}.manifest", manifest_content)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"Drop_Into_SteamTools_{appid}.zip")
        
        embed = discord.Embed(title=f"✅ Ready for {name}", color=0x9b59b6)
        embed.description = (
            "**Zero-Work Instructions:**\n"
            "1. Open the ZIP.\n"
            "2. Drag the **scripts** and **manifests** folders into your **SteamTools/GreenLuma** folder.\n"
            "3. If Windows asks to merge folders, click **Yes**."
        )
        await ctx.send(embed=embed, file=file)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Limit: 4 per day.")

bot.run(TOKEN)
