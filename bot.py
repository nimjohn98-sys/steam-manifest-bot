import discord
from discord.ext import commands
import requests
import io

TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def snap(ctx, app_id: str):
    """Takes a screenshot using an external API instead of local Chromium."""
    await ctx.send(f"📸 Requesting external screenshot for App ID `{app_id}`...")

    # We tell the API to look at the site and wait 3 seconds for it to load
    # This URL mimics what a user sees after searching
    target_url = f"https://manifest.youngzm.com/?search={app_id}"
    screenshot_api_url = f"https://image.thum.io/get/width/1200/viewportWidth/1200/wait/3000/{target_url}"

    try:
        response = requests.get(screenshot_api_url, timeout=20)
        
        if response.status_code == 200:
            data = io.BytesIO(response.content)
            file = discord.File(data, filename="site_view.png")
            await ctx.send(content=f"🖼️ Here is what the website looks like for `{app_id}`:", file=file)
        else:
            await ctx.send("❌ The screenshot service is currently busy. Try again in a minute.")
            
    except Exception as e:
        await ctx.send(f"⚠️ Failed to get screenshot: {e}")

@bot.command()
async def gen(ctx, app_id: str):
    # (Keep your 'gen' code from the previous "No-Browser" version here)
    pass

bot.run(TOKEN)
