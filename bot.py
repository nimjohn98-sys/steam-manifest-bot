
import discord
from discord.ext import commands
import asyncio
from playwright.async_api import async_playwright
import io

# Secure your token - Discord will likely revoke this one since it's public
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot active: {bot.user}')

@bot.command()
async def snap(ctx, app_id: str):
    """Takes a screenshot of the search page to debug issues."""
    await ctx.send(f"📸 Capturing browser state for App ID `{app_id}`...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto("https://manifest.youngzm.com/", wait_until="networkidle")
            
            # Perform the search so we see the results in the screenshot
            await page.fill("input[type='text']", app_id)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2000) # Give it a moment to render results
            
            # Take screenshot
            screenshot_bytes = await page.screenshot(full_page=True)
            await browser.close()
            
            # Send to Discord
            data = io.BytesIO(screenshot_bytes)
            await ctx.send(file=discord_file := discord.File(data, filename="debug_snap.png"))
            
        except Exception as e:
            await ctx.send(f"❌ Failed to take screenshot: {e}")
            await browser.close()

@bot.command()
async def gen(ctx, app_id: str):
    """The main command to download the manifest."""
    msg = await ctx.send(f"⚡ Searching for `{app_id}`...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        
        try:
            await page.goto("https://manifest.youngzm.com/", wait_until="domcontentloaded")
            await page.fill("input[type='text']", app_id)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(1500)

            # Look for the download trigger
            # This targets the 'download' icon or link text specifically
            async with page.expect_download() as download_info:
                # We click the specific entry for the app_id
                await page.click(f"text={app_id}") 
                # Then click the actual download button/icon that appears
                await page.click("i.fa-download, a[title*='Download']")
            
            download = await download_info.value
            path = await download.path()
            
            with open(path, "rb") as f:
                discord_file = discord.File(io.BytesIO(f.read()), filename=f"{app_id}.zip")
                await msg.edit(content=f"✅ Found manifest for `{app_id}`!")
                await ctx.send(file=discord_file)
            
            await browser.close()

        except Exception as e:
            await msg.edit(content=f"❌ Error: Could not find or download `{app_id}`. Use `!snap {app_id}` to see why.")
            await browser.close()

bot.run(TOKEN)
