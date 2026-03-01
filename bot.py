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
        return "Game"
    return "Game"

@bot.event
async def on_ready():
    print(f'🚀 Bot Online: {bot.user}')
    print(f'Listening for !search and !gen commands...')

@bot.command()
async def search(ctx, *, game_name: str):
    """Finds the AppID for a game by its name."""
    search_url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(game_name)}&l=english&cc=US"
    
    async with ctx.typing():
        try:
            r = requests.get(search_url).json()
            if r.get('total') > 0:
                top_result = r['items'][0]
                name = top_result['name']
                appid = top_result['id']
                
                embed = discord.Embed(title="🔍 Steam Search Results", color=0x3498db)
                embed.add_field(name="Top Match", value=name, inline=True)
                embed.add_field(name="AppID", value=f"`{appid}`", inline=True)
                embed.set_footer(text=f"Use '!gen {appid}' to get the files.")
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ No games found with that name.")
        except:
            await ctx.send("⚠️ Search error occurred.")

@bot.command()
@commands.cooldown(4, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    """Generates a ZIP with folders for direct drag-and-drop into SteamTools."""
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Please provide a numeric AppID.")

    async with ctx.typing():
        name = get_game_name(appid)
        
        lua_content = f'add_app({appid}, "{name}")'
        manifest_content = f"""{{
    "appmanifest": {{
        "appid": "{appid}",
        "name": "{name}",
        "StateFlags": "4"
    }}
}}"""

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            # Matches SteamTools/GreenLuma folder structure
            zf.writestr(f"scripts/{appid}.lua", lua_content)
            zf.writestr(f"manifests/{appid}.manifest", manifest_content)
        
        zip_buffer.seek(0)
        file = discord.File(fp=zip_buffer, filename=f"Drag_To_SteamTools_{appid}.zip")
        
        embed = discord.Embed(title=f"📦 Easy-Drop for {name}", color=0x3498db)
        embed.description = (
            "**Zero-Work Instructions:**\n"
            "1. Open the ZIP.\n"
            "2. Drag the **scripts** and **manifests** folders directly into your **SteamTools folder**.\n"
            "3. Click **Yes** when Windows asks to merge folders.\n\n"
            "*This ensures files land in the right spot without you opening sub-folders.*"
        )
        await ctx.send(embed=embed, file=file)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Daily limit reached. You can generate more in {int(error.retry_after // 3600)}h.")

bot.run(TOKEN)
