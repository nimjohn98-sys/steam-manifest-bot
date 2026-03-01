import discord
from discord.ext import commands
import asyncio
from playwright.async_api import async_playwright
import io

# REPLACE THIS if it stops working (Discord often resets public tokens)
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

async def get_manifest_file(app_id):
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        
        try:
            # 1. Load the site
            await page.goto("https://manifest.youngzm.com/", wait_until="domcontentloaded")

            # 2. Type into the search bar
            # The site uses a standard search input
            await page.fill("input[type='text']", app_id)
            await page.keyboard.press("Enter")

            # 3. Click the Download Button
            # We look for a link or button that contains the download icon or text
            # Based on the site's structure, we target the first 'download' action
            download_button_selector = "a[title*='Download'], .download-btn, i.fa-download"
            
            # Wait briefly for the search result to filter the list
            await page.wait_for_timeout(1000) 

            # Start waiting for the download event before clicking
            async with page.expect_download() as download_info:
                # Click the first available download link for that App ID
                await page.click(f"text={app_id}") # Clicks the file name first to select
                await page.click(download_button_selector) # Then clicks download
            
            download = await download_info.value
            
            # 4. Stream the file into memory
            file_path = await download.path()
            with open(file_path, "rb") as f:
                content = f.read()
            
            await browser.close()
            return content

        except Exception as e:
            print(f"Error: {e}")
            await browser.close()
            return None

@bot.command()
async def gen(ctx, app_id: str):
    msg = await ctx.send(f"⚡ **Processing:** Searching for `{app_id}` and clicking download...")
    
    file_bytes = await get_manifest_file(app_id)
    
    if file_bytes:
        data = io.BytesIO(file_bytes)
        # Check if the file is valid (not an empty error page)
        if len(file_bytes) < 500:
            await msg.edit(content=f"❌ The file for `{app_id}` appears to be empty or restricted on the site.")
        else:
            discord_file = discord.File(data, filename=f"{app_id}.zip")
            await msg.edit(content=f"✅ **Success!** Downloaded manifest for `{app_id}`.")
            await ctx.send(file=discord_file)
    else:
        await msg.edit(content=f"❌ **Failed:** Could not find the download button for `{app_id}`.")

bot.run(TOKEN)
