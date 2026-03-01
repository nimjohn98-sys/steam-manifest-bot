import asyncio
from playwright.async_api import async_playwright

async def download_steam_manifest(app_id):
    # Change this to the actual page where the button is
    url = f"https://steamdb.info/app/{app_id}/manifests/" 

    async with async_playwright() as p:
        # Launch a real browser (Headless=False lets you see it happen)
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()

        print(f"🚀 Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")

        try:
            # --- THE CLICK LOGIC ---
            # This searches for a button that says 'Download' or has the right class
            # You can change 'text="Download"' to match the actual button text
            print("🖱️ Locating download button...")
            
            # Wait for the button to be visible
            button = page.locator('button:has-text("Download"), a:has-text("Download")').first
            
            # Record the download event
            async with page.expect_download() as download_info:
                await button.click()
                print("✅ Button clicked!")
            
            download = await download_info.value
            path = f"./{app_id}_manifest.lua"
            await download.save_as(path)
            print(f"💾 File saved successfully to: {path}")

        except Exception as e:
            print(f"❌ Error during click/download: {e}")
            # If it fails, take a screenshot so we can see why
            await page.screenshot(path="error_screen.png")
            print("📸 Error screenshot saved as 'error_screen.png'")

        await browser.close()

if __name__ == "__main__":
    APP_ID = "367520" # Replace with your AppID
    asyncio.run(download_steam_manifest(APP_ID))
