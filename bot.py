import discord
from discord.ext import commands
import random
import re
import io
import importlib
import scraper_logic  # Make sure scraper_logic.py is in the same folder

# --- 🟢 FINAL CONFIGURATION 🟢 ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
OWNER_ID = 1241307424196001928

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- THE SELF-CODING ALGORITHM (GENETIC PROGRAMMING) ---
def mutate_logic():
    """Rewrites scraper_logic.py with new 'mutated' DNA."""
    with open("scraper_logic.py", "r", encoding="utf-8") as f:
        code = f.read()

    # Potential 'Genes' to try
    agents = [
        "'Steam/1.0'", 
        "'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'", 
        "'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'", 
        "'PostmanRuntime/7.32.3'"
    ]
    libraries = ["cloudscraper.create_scraper()", "requests.Session()"]
    
    # Randomly mutate the code using Regex
    code = re.sub(r"header_val = .*", f"header_val = {random.choice(agents)}", code)
    code = re.sub(r"timeout_val = .*", f"timeout_val = {random.randint(5, 45)}", code)
    code = re.sub(r"scraper = .*", f"scraper = {random.choice(libraries)}", code)

    with open("scraper_logic.py", "w", encoding="utf-8") as f:
        f.write(code)

@bot.event
async def on_ready():
    print(f"✅ Full Autonomous Bot is Online: {bot.user}")

@bot.command()
async def fix(ctx):
    """Evolves the bot's code until it successfully bypasses the target."""
    if ctx.author.id != OWNER_ID: return

    msg = await ctx.send("🧬 **Evolution in progress...** Mutating local DNA.")
    
    # Try up to 20 mutations to find a working 'species' of code
    for i in range(20):
        mutate_logic()
        importlib.reload(scraper_logic) # This is the "Code Itself" magic
        
        try:
            # Test mutation with a common AppID (e.g., CS2 - 730)
            test_data = scraper_logic.download_manifest("730")
            if test_data.startswith(b'PK'): # ZIP files start with 'PK'
                return await msg.edit(content=f"✅ **Success!** Mutation #{i+1} coded a working bypass.")
        except Exception:
            continue
            
    await msg.edit(content="❌ **Evolution failed.** All 20 mutations failed to bypass the site.")

@bot.command()
async def gen(ctx, app_id: str):
    """Executes the current version of the code."""
    try:
        data = scraper_logic.download_manifest(app_id)
        if data.startswith(b'PK'):
            file = discord.File(io.BytesIO(data), f"{app_id}.zip")
            await ctx.send(f"📦 **Manifest Found!** (AppID: {app_id})", file=file)
        else:
            await ctx.send("🚨 **Dead Code.** The site blocked this version. Use `!fix` to evolve.")
    except Exception as e:
        await ctx.send(f"❌ **Crash:** `{e}`. System requires a `!fix`.")

bot.run(TOKEN)