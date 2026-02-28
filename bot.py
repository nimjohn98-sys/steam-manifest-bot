import discord
from discord.ext import commands
import requests
from urllib.parse import quote

# --- CONFIGURATION ---
# IMPORTANT: Reset your token in the Discord Dev Portal since it is public!
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Manifest Bot is online as {bot.user}')
    print('Use !gen <game name> to start.')

@bot.command()
async def gen(ctx, *, game_name: str):
    """Searches Steam and provides Manifest Downloader links."""
    
    # 1. Search Steam for the Game Name to get the App ID
    search_url = f"https://store.steampowered.com/api/storesearch/?term={quote(game_name)}&l=english&cc=US"
    
    try:
        response = requests.get(search_url)
        data = response.json()

        if not data.get('items'):
            await ctx.send(f"❌ No games found for `{game_name}`.")
            return

        # 2. Extract top result data
        game = data['items'][0]
        name = game['name']
        app_id = game['id']
        img = game.get('tiny_image')

        # 3. Construct the Manifest Downloader Link
        # This points to the specific URL you requested
        manifest_url = f"https://manifest.youngzm.com/#/{app_id}"
        steamdb_url = f"https://steamdb.info/app/{app_id}/depots/"

        # 4. Create the Discord Embed
        embed = discord.Embed(
            title=name,
            description=f"Manifest and Depot tools for App ID: `{app_id}`",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🛠️ Manifest Tool", 
            value=f"[**Open Manifest Downloader**]({manifest_url})", 
            inline=False
        )
        
        embed.add_field(
            name="📊 SteamDB Reference", 
            value=f"[View Depots on SteamDB]({steamdb_url})", 
            inline=False
        )
        
        embed.add_field(
            name="💻 Console Command",
            value=f"```download_depot {app_id} <depot_id> <manifest_id>```",
            inline=False
        )

        if img:
            embed.set_thumbnail(url=img)

        embed.set_footer(text="Powered by manifest.youngzm.com")

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

bot.run(TOKEN)
