import discord
from discord.ext import commands
import requests
import io
from urllib.parse import quote

# --- CONFIGURATION ---
# REMINDER: Reset this token in the Discord Dev Portal!
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Manifest ZIP Bot is ready: {bot.user}')

@bot.command()
async def gen(ctx, *, game_name: str):
    """Searches Steam and uploads the Manifest ZIP directly to Discord."""
    await ctx.send(f"📦 Fetching manifest ZIP for `{game_name}`...")

    try:
        # 1. Get App ID from Steam Store
        search_url = f"https://store.steampowered.com/api/storesearch/?term={quote(game_name)}&l=english&cc=US"
        search_res = requests.get(search_url).json()

        if not search_res.get('items'):
            return await ctx.send("❌ Game not found on Steam.")

        game = search_res['items'][0]
        app_id = game['id']
        name = game['name']

        # 2. Fetch the ZIP from the manifest provider
        # Note: We use the API endpoint that the website calls internally
        download_url = f"https://manifest.youngzm.com/api/download/{app_id}"
        
        response = requests.get(download_url, stream=True)

        if response.status_code != 200:
            # Fallback: Some providers use a different structure
            return await ctx.send(f"⚠️ Could not generate ZIP for `{name}`. The manifest might not be cached yet.")

        # 3. Send the file directly from memory (no saving to disk required)
        zip_file = io.BytesIO(response.content)
        discord_file = discord.File(zip_file, filename=f"Manifest_{app_id}_{name.replace(' ', '_')}.zip")

        embed = discord.Embed(
            title="Manifest Generated",
            description=f"Successfully pulled manifest files for **{name}**.",
            color=discord.Color.blue()
        )
        embed.add_field(name="App ID", value=f"`{app_id}`")
        
        await ctx.send(embed=embed, file=discord_file)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

bot.run(TOKEN)
