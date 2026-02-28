import discord
from discord import app_commands
from discord.ext import commands
import random
import re
import io
import importlib
import scraper_logic # Ensure scraper_logic.py is in the same folder

# --- 🟢 CONFIGURATION 🟢 ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
OWNER_ID = 1241307424196001928

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # This syncs the slash commands to Discord
        await self.tree.sync()
        print(f"✅ Slash commands synced for {self.user}")

bot = MyBot()

# --- THE EVOLUTIONARY ALGORITHM ---
def mutate_logic():
    with open("scraper_logic.py", "r", encoding="utf-8") as f:
        code = f.read()

    agents = ["'Steam/1.0'", "'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'", "'PostmanRuntime/7.32.3'"]
    libraries = ["cloudscraper.create_scraper()", "requests.Session()"]
    
    code = re.sub(r"header_val = .*", f"header_val = {random.choice(agents)}", code)
    code = re.sub(r"timeout_val = .*", f"timeout_val = {random.randint(5, 45)}", code)
    code = re.sub(r"scraper = .*", f"scraper = {random.choice(libraries)}", code)

    with open("scraper_logic.py", "w", encoding="utf-8") as f:
        f.write(code)

# --- 🛰️ SLASH COMMANDS ---

@bot.tree.command(name="fix", description="Evolve the bot's code to fix scraper errors.")
async def fix(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Owner only!", ephemeral=True)

    await interaction.response.defer() # Gives the bot time to "think" (mutate)
    
    for i in range(20):
        mutate_logic()
        importlib.reload(scraper_logic)
        try:
            test_data = scraper_logic.download_manifest("730")
            if test_data.startswith(b'PK'):
                return await interaction.followup.send(f"✅ **Success!** Mutation #{i+1} found a working bypass.")
        except:
            continue
            
    await interaction.followup.send("❌ **Evolution failed.** The site is still blocking us.")

@bot.tree.command(name="gen", description="Generate a Steam manifest ZIP.")
@app_commands.describe(app_id="The Steam AppID (e.g., 730 for CS2)")
async def gen(interaction: discord.Interaction, app_id: str):
    await interaction.response.defer()
    try:
        data = scraper_logic.download_manifest(app_id)
        if data.startswith(b'PK'):
            file = discord.File(io.BytesIO(data), f"{app_id}.zip")
            await interaction.followup.send(f"📦 **Manifest Found!** (AppID: {app_id})", file=file)
        else:
            await interaction.followup.send("🚨 **Dead Code.** Use `/fix` to evolve a new version.")
    except Exception as e:
        await interaction.followup.send(f"❌ **Crash:** `{e}`. System requires a `/fix`.")

bot.run(TOKEN)