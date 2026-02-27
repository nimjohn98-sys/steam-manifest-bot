import discord
from discord.ext import commands
import requests

# Define intents
intents = discord.Intents.default()
intents.messages = True

# Create the bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def gen(ctx, *, app_id: str):
    """Fetch Steam manifest for a given app ID."""
    url = f'https://manifest.youngzm.com/{app_id}'
    response = requests.get(url)

    if response.status_code == 200:
        await ctx.send(f'Manifest data: {response.text}')
    else:
        await ctx.send('Error fetching manifest data.')

# Run the bot
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
bot.run(TOKEN)