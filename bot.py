import discord
from discord.ext import commands
import requests
import io

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://manifest.youngzm.com/"
}

@bot.event
async def on_ready():
    print(f'✅ Bot is online as {bot.user.name}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ **Cooldown!** Please wait `{error.retry_after:.1f}`s.")

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def gen(ctx, *, search_term: str):
    """Search for a game name, find ID, and download manifest zip."""
    
    # 1. If user gave a number, use it. If not, search Steam.
    if search_term.isdigit():
        app_id = search_term
        game_name = f"AppID {app_id}"
    else:
        await ctx.send(f"🔍 Searching Steam for `{search_term}`...")
        search_url = f"https://store.steampowered.com/api/storesearch/?term={search_term}&l=english&cc=US"
        try:
            r = requests.get(search_url).json()
            if r.get('total', 0) > 0:
                app_id = str(r['items'][0]['id'])
                game_name = r['items'][0]['name']
            else:
                return await ctx.send(f"❌ Could not find a game named `{search_term}` on Steam.")
        except:
            return await ctx.send("🚨 Steam search failed. Try using the ID number directly.")

    # 2. Try downloading the ZIP
    await ctx.send(f"🛠️ Found **{game_name}** (`{app_id}`). Fetching manifest...")

    # We try the AppID AND common Depot IDs (AppID + 1 is very common)
    ids_to_try = [app_id, str(int(app_id) + 1)]
    
    success = False
    for target_id in ids_to_try:
        api_url = f"https://manifest.youngzm.com/api/download/{target_id}"
        try:
            response = requests.get(api_url, headers=HEADERS, timeout=25)
            # Only accept if it's a real file (usually > 1KB)
            if response.status_code == 200 and len(response.content) > 1000:
                file_data = io.BytesIO(response.content)
                zip_file = discord.File(file_data, filename=f"{game_name.replace(' ', '_')}_{target_id}.zip")
                await ctx.send(content=f"✅ **Manifest Ready!**\nGame: **{game_name}**\nID used: `{target_id}`", file=zip_file)
                success = True
                break
        except:
            continue

    if not success:
        await ctx.send(f"❌ **Not Found:** No valid zip found for **{game_name}** on the manifest site.\n🔗 Try manually: https://manifest.youngzm.com/?query={app_id}")

# Replace with your token
bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
