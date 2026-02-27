import discord
from discord.ext import commands
import requests
import zipfile
import io

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Create the bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Steam App ID database
STEAM_GAMES = {
    'csgo': 730,
    'counter-strike': 730,
    'dota 2': 570,
    'pubg': 578080,
    'hl2': 220,
    'half-life 2': 220,
    'tf2': 440,
    'team fortress 2': 440,
    'l4d2': 550,
    'left 4 dead 2': 550,
}

def get_app_id(game_input):
    """Convert game name to app ID or return app ID if already numeric"""
    if game_input.isdigit():
        return int(game_input)
    
    game_lower = game_input.lower()
    if game_lower in STEAM_GAMES:
        return STEAM_GAMES[game_lower]
    
    return None

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def gen(ctx, *, game_input: str):
    """Fetch Steam manifest for a given app ID or game name.
    Usage: !gen <app_id or game_name>
    """
    try:
        await ctx.send("🔍 Fetching manifest...")
        
        # Convert game name to app ID
        app_id = get_app_id(game_input)
        
        if app_id is None:
            await ctx.send(f"❌ Could not find game: `{game_input}`\nUse `!list` to see supported games or provide an App ID.")
            return
        
        # Fetch manifest
        url = f'https://manifest.youngzm.com/{app_id}'
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # Create zip file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(f'manifest_{app_id}.lua', response.text)
            zip_buffer.seek(0)
            
            # Send to Discord
            await ctx.send(
                f"✅ Manifest for App ID `{app_id}`",
                file=discord.File(zip_buffer, filename=f'manifest_{app_id}.zip')
            )
        else:
            await ctx.send(f'❌ Error fetching manifest data for App ID: `{app_id}`')
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command()
async def help(ctx):
    """Show help information about the bot."""
    embed = discord.Embed(
        title="🤖 Steam Manifest Bot Help",
        description="Fetch Steam game manifests from manifest.youngzm.com",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="!gen <app_id or game_name>",
        value="Fetch and download a manifest zip file\nExample: `!gen csgo` or `!gen 730`",
        inline=False
    )
    
    embed.add_field(
        name="!list",
        value="Show all supported game names",
        inline=False
    )
    
    embed.add_field(
        name="!help",
        value="Show this help message",
        inline=False
    )
    
    embed.set_footer(text="💡 Tip: You can use either the game name or App ID")
    
    await ctx.send(embed=embed)

@bot.command()
async def list(ctx):
    """List all supported game names."""
    games_list = "\n".join([f"• **{name}** (ID: {app_id})" for name, app_id in sorted(STEAM_GAMES.items())])
    
    embed = discord.Embed(
        title="📋 Supported Games",
        description=games_list,
        color=discord.Color.green()
    )
    
    await ctx.send(embed=embed)

# Run the bot
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
bot.run(TOKEN)