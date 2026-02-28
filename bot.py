import discord
from discord.ext import commands
import requests

# --- CONFIGURATION ---
# Note: Keep this private in the future!
DISCORD_TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot is online!')
    print(f'Logged in as: {bot.user.name}')
    print('Type !appid <game name> in Discord to test.')

@bot.command()
async def appid(ctx, *, game_name: str):
    """Searches Steam for an App ID and Manifest info using public API."""
    
    # Steam's public search suggestion endpoint
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    
    try:
        response = requests.get(search_url)
        data = response.json()

        if not data.get('items'):
            await ctx.send(f"❌ No games found for `{game_name}`.")
            return

        # Extract top result
        game = data['items'][0]
        name = game['name']
        game_id = game['id']
        price = game.get('price', {}).get('final', 'Free/Unknown')
        
        # Convert price from cents if it's a number
        if isinstance(price, int):
            price = f"${price / 100:.2f}"

        # Build the response embed
        embed = discord.Embed(
            title=name, 
            url=f"https://store.steampowered.com/app/{game_id}",
            color=discord.Color.blue()
        )
        embed.add_field(name="App ID", value=f"`{game_id}`", inline=True)
        embed.add_field(name="Current Price", value=f"{price}", inline=True)
        
        # Add a link to SteamDB for manifest/depot info
        embed.add_field(
            name="Manifest Info", 
            value=f"[View on SteamDB](https://steamdb.info/app/{game_id}/depots/)", 
            inline=False
        )
        
        if game.get('tiny_image'):
            embed.set_thumbnail(url=game['tiny_image'])
            
        embed.set_footer(text="Data fetched via Steam Storefront API")

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"⚠️ An error occurred: {e}")

bot.run(DISCORD_TOKEN)
