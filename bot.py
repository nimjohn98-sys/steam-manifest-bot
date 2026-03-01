import discord
from discord.ext import commands
import zipfile
import io
import requests
import urllib.parse

# --- CONFIG ---
# If the bot gives an "Unauthorized" error, reset your token at the Discord Dev Portal.
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg' 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

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

# --- CUSTOM HELP ---
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🛠️ SteamTools Bot Help", color=0xf1c40f)
    embed.add_field(name="`!search [Name]`", value="Find the AppID for any game.", inline=False)
    embed.add_field(name="`!gen [AppID]`", value="Get the ZIP (Limit: 5 per day).", inline=False)
    embed.description = "**Installation:** Open the ZIP and drag the **scripts** and **manifests** folders into your SteamTools folder."
    await ctx.send(embed=embed)

# --- SEARCH ---
@bot.command()
async def search(ctx, *, game_name: str):
    search_url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(game_name)}&l=english&cc=US"
    async with ctx.typing():
        try:
            r = requests.get(search_url).json()
            if r.get('total') > 0:
                item = r['items'][0]
                await ctx.send(f"🔍 **Result:** {item['name']} | **AppID:** `{item['id']}`\nType `!gen {item['id']}`")
            else:
                await ctx.send("❌ Game not found.")
        except:
            await ctx.send("⚠️ Steam API error.")

# --- GENERATE (5 per day limit) ---
@bot.command()
@commands.cooldown(5, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Use a numeric AppID.")

    async with ctx.typing():
        name = get_game_name(appid)
        
        # Folder-structured content
        lua_content = f'add_app({appid}, "{name}")'
        manifest_content = f'{{\n    "appmanifest": {{\n        "appid": "{appid}",\n        "name": "{name}",\n        "StateFlags": "4"\n    }}\n}}'

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            # This creates the folders automatically in the ZIP
            zf.writestr(f"scripts/{appid}.lua", lua_content)
            zf.writestr(f"manifests/{appid}.manifest", manifest_content)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"SteamTools_{appid}.zip")
        
        await ctx.send(f"✅ **ZIP Ready for {name}** (Usage: {ctx.command.get_cooldown_rate(ctx)}/5 today)", file=file)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        hours = int(error.retry_after // 3600)
        await ctx.send(f"⏳ **Limit Reached!** You can generate 5 games every 24 hours. Try again in {hours}h.")

bot.run(TOKEN)
