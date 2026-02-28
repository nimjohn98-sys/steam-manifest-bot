import discord
from discord.ext import commands
import requests
import io

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# These headers are MANDATORY. Without them, the site returns a 403 Forbidden.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://manifest.youngzm.com/",
    "Accept": "application/json, text/plain, */*"
}

@bot.event
async def on_ready():
    print(f'✅ Bot Fixed & Online: {bot.user.name}')

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def gen(ctx, *, app_id: str):
    """Hits the site's internal download trigger directly."""
    await ctx.send(f"🔍 Accessing manifest database for `{app_id}`...")

    # This is the EXACT URL triggered by the 'Download' button in the search results
    # It bypasses the need to 'click' the UI.
    download_url = f"https://manifest.youngzm.com/api/download/{app_id}"

    try:
        # We use a session to maintain the connection like a real browser
        with requests.Session() as session:
            response = session.get(download_url, headers=HEADERS, timeout=30)
            
            # Check if we actually got a ZIP file and not an error page
            if response.status_code == 200 and len(response.content) > 500:
                # Double check content type to ensure it's a zip
                if "application/zip" in response.headers.get('Content-Type', '').lower() or response.content[:2] == b'PK':
                    file_data = io.BytesIO(response.content)
                    zip_file = discord.File(file_data, filename=f"manifest_{app_id}.zip")
                    
                    await ctx.send(content=f"✅ **File Grabbed!** Here is your manifest for `{app_id}`:", file=zip_file)
                else:
                    await ctx.send(f"❌ The site returned data, but it wasn't a valid ZIP. The manifest for `{app_id}` might be empty or restricted.")
            else:
                await ctx.send(f"❌ **Download Failed.** The website search returned no file for `{app_id}`. (Status: {response.status_code})")
                
    except Exception as e:
        await ctx.send(f"🚨 **Technical Error:** {str(e)}")

# Your Token
bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
