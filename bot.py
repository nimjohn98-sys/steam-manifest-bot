import discord
from discord.ext import commands
import requests
from steam.client import SteamClient

# --- CONFIGURATION ---
DISCORD_TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize Steam Client (Anonymous login)
steam_client = SteamClient()
steam_client.anonymous_login()

@bot.event
async def on_ready():
    print(f'✅ Bot active: {bot.user}')

@bot.command()
async def gen(ctx, *, game_name: str):
    """Fetches manifest/depot info and sends it as a file/message."""
    await ctx.send(f"🔍 Searching Steam for `{game_name}`...")

    # 1. Get App ID from Steam Store
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    try:
        res = requests.get(search_url).json()
        if not res.get('items'):
            return await ctx.send("❌ Game not found.")
        
        game = res['items'][0]
        app_id = game['id']
        name = game['name']

        # 2. Fetch Product Info from Steam (Headless)
        # This gets the actual technical data usually seen on SteamDB
        app_info = steam_client.get_product_info(apps=[app_id])
        
        if not app_info or 'apps' not in app_info:
            return await ctx.send("❌ Could not fetch technical manifest data.")

        depots = app_info['apps'][app_id].get('depots', {})
        
        manifest_data = f"MANIFEST DATA FOR: {name} (AppID: {app_id})\n"
        manifest_data += "="*40 + "\n\n"

        found_depots = False
        for d_id, d_info in depots.items():
            if d_id.isdigit():
                manifest = d_info.get('manifests', {}).get('public', 'N/A')
                if manifest != 'N/A':
                    found_depots = True
                    manifest_data += f"Depot ID: {d_id}\n"
                    manifest_data += f"Manifest: {manifest}\n"
                    manifest_data += f"Command: download_depot {app_id} {d_id} {manifest}\n"
                    manifest_data += "-"*20 + "\n"

        if not found_depots:
            return await ctx.send(f"❌ No public manifests found for {name}.")

        # 3. Create a temporary text file and send it
        with open("manifest_info.txt", "w", encoding="utf-8") as f:
            f.write(manifest_data)

        file = discord.File("manifest_info.txt", filename=f"{name}_manifests.txt")
        await ctx.send(content=f"✅ Here is the manifest data for **{name}**:", file=file)

    except Exception as e:
        await ctx.send(f"⚠️ Error: {str(e)}")

bot.run(DISCORD_TOKEN)
