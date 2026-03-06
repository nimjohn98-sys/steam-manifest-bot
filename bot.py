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

# Optimized helper to get game name
def get_game_name(appid):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        # Set a timeout so the bot doesn't get stuck forever
        r = requests.get(url, timeout=5).json()
        if r and r.get(str(appid), {}).get('success'):
            return r[str(appid)]['data']['name']
    except Exception as e:
        print(f"Steam API Error: {e}")
    return "Steam_Game"

@bot.event
async def on_ready():
    print(f'🚀 Bot Online: {bot.user}')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🛠️ SteamTools Bot Help", color=0xf1c40f)
    embed.add_field(name="`!search [Name]`", value="Find the AppID.", inline=False)
    embed.add_field(name="`!gen [AppID]`", value="Get the ZIP (Limit: 5/day).", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def search(ctx, *, game_name: str):
    search_url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(game_name)}&l=english&cc=US"
    try:
        r = requests.get(search_url, timeout=5).json()
        if r.get('total') > 0:
            item = r['items'][0]
            await ctx.send(f"🔍 **Result:** {item['name']} | **AppID:** `{item['id']}`")
        else:
            await ctx.send("❌ Game not found.")
    except:
        await ctx.send("⚠️ Search timed out.")

@bot.command()
@commands.cooldown(5, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Enter a numeric ID.")

    # We use a context manager to ensure the typing stops
    async with ctx.typing():
        try:
            name = get_game_name(appid)
            
            # Prepare contents
            lua = f'add_app({appid}, "{name}")'
            manifest = f'{{"appmanifest":{{"appid":"{appid}","name":"{name}","StateFlags":"4"}}}}'

            # Create ZIP in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"scripts/{appid}.lua", lua)
                zf.writestr(f"manifests/{appid}.manifest", manifest)
            
            zip_buffer.seek(0)
            
            # Send file
            file = discord.File(fp=zip_buffer, filename=f"SteamTools_{appid}.zip")
            await ctx.send(content=f"✅ **{name}** ZIP generated!", file=file)
            
        except Exception as e:
            print(f"Gen Error: {e}")
            await ctx.send(f"⚠️ Failed to create ZIP: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Limit reached. Try again in {int(error.retry_after // 3600)}h.")
    else:
        print(f"Error: {error}")

bot.run(TOKEN)
