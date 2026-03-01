import discord
from discord.ext import commands
import asyncio
from playwright.async_api import async_playwright
import os

# --- CREDENTIALS ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
MY_ID = 123456789012345678  # <--- RIGHT-CLICK YOUR NAME IN DISCORD TO GET THIS ID

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents, owner_id=MY_ID)

async def get_manifest(app_id):
    """The 'Fix': Mimics a real user to find and click the download button."""
    url = f"https://steamdb.info/app/{app_id}/manifests/"
    
    async with async_playwright() as p:
        # We use a real Chromium browser to handle JavaScript buttons
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"🚀 Navigating to AppID: {app_id}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Find button by text (Download)
            # This handles cases where the site uses 'Download' as a button or a link
            btn = page.locator('button:has-text("Download"), a:has-text("Download")').first
            await btn.wait_for(state="visible", timeout=10000)
            
            # Start tracking the download before we click
            async with page.expect_download() as download_info:
                await btn.click()
            
            download = await download_info.value
            path = f"{app_id}.lua"
            await download.save_as(path)
            return True, path
            
        except Exception as e:
            # JPEG Fix: Snap a full-page photo to see what went wrong (Captcha/403/Missing Button)
            img_path = f"error_{app_id}.jpg"
            await page.screenshot(path=img_path, type="jpeg", full_page=True)
            return False, img_path
            
        finally:
            await browser.close()

@bot.command()
@commands.is_owner() # This ensures ONLY YOU can trigger the bot
async def fetch(ctx, app_id: str):
    await ctx.send(f"🔍 Accessing manifest data for {app_id}...")
    
    success, result = await get_manifest(app_id)
    
    if success:
        await ctx.send(f"✅ **Success!** Manifest delivered:", file=discord.File(result))
    else:
        await ctx.send(f"❌ **Blocked or Error.** Sending JPEG report for analysis:", file=discord.File(result))
    
    # Clean up files from your computer to save space
    if os.path.exists(result):
        os.remove(result)

@bot.event
async def on_ready():
    print(f"🟢 {bot.user} is active. Only Owner ID {MY_ID} can use !fetch")

bot.run(TOKEN)
