import discord
from discord.ext import commands
import zipfile
import io
import requests

# --- CONFIG ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg' 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Simple cache to speed things up and avoid "stuck typing"
def get_game_name(appid):
    try:
        # Using a faster, more reliable endpoint
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic"
        r = requests.get(url, timeout=5).json()
        if r and r.get(str(appid), {}).get('success'):
            return r[str(appid)]['data']['name']
    except:
        pass
    return f"App_{appid}"

@bot.event
async def on_ready():
    print(f'🚀 Bot is live as {bot.user}')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📦 SteamTools Generator", color=0x3498db)
    embed.add_field(name="Commands", value="`!search [game]`\n`!gen [appid]`", inline=False)
    embed.add_field(name="How to use", value="1. Open ZIP\n2. Drag **scripts** & **manifests** to SteamTools folder\n3. Click 'Yes' to merge.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def search(ctx, *, query: str):
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
    try:
        r = requests.get(url, timeout=5).json()
        if r.get('items'):
            game = r['items'][0]
            await ctx.send(f"✅ Found: **{game['name']}** | ID: `{game['id']}`")
        else:
            await ctx.send("❌ No game found.")
    except:
        await ctx.send("⚠️ Steam search busy, try again.")

@bot.command()
@commands.cooldown(5, 86400, commands.BucketType.user)
async def gen(ctx, appid: str):
    if not appid.isdigit():
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Use a number.")

    async with ctx.typing():
        try:
            name = get_game_name(appid)
            
            # Create the files exactly as they appear on manifest websites
            lua = f'add_app({appid}, "{name}")'
            manifest = f'{{\n  "appmanifest": {{\n    "appid": "{appid}",\n    "name": "{name}",\n    "StateFlags": "4"\n  }}\n}}'

            # Build the ZIP with the folder structure
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                # This mimics the website layout for easy drag-and-drop
                zf.writestr(f"scripts/{appid}.lua", lua)
                zf.writestr(f"manifests/{appid}.manifest", manifest)
            
            zip_buffer.seek(0)
            file = discord.File(fp=zip_buffer, filename=f"Manifest_{appid}.zip")
            
            await ctx.send(f"✅ **{name}** (5 daily limit)", file=file)
            
        except Exception as e:
            await ctx.send(f"⚠️ Error: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Daily limit reached. Try again in {int(error.retry_after // 3600)}h.")

bot.run(TOKEN)
