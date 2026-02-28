import discord
from discord.ext import commands
import requests
import io
import os
from github import Github
from google import genai
from googlesearch import search

# --- 🟢 YOUR COMPLETED CONFIGURATION 🟢 ---
DISCORD_TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
GITHUB_TOKEN = "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"
GEMINI_KEY = "AIzaSyBSGnbQBRfS65dN2g8GphxGA8EevxSSfzs"
REPO_NAME = "nimjohn98-sys/steam-manifest-bot"
LOGIC_FILE = "scraper_logic.py"
OWNER_ID = 1241307424196001928  # <--- YOUR ID IS NOW HARDCODED

# Initialize Clients
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
ai_client = genai.Client(api_key=GEMINI_KEY)

# --- GITHUB ENGINE ---
def push_to_github(code, message="🛠️ Automated Update"):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(LOGIC_FILE, ref="main")
    repo.update_file(contents.path, message, code, contents.sha, branch="main")
    return f"https://github.com/{REPO_NAME}/commit/main"

# This function gets overwritten when you run !update
def download_manifest(app_id):
    raise Exception("Brain not loaded. Type !update to sync with GitHub.")

@bot.event
async def on_ready():
    print(f"✅ Bot is live as {bot.user}")

# --- COMMAND: !GEN (Scrape Manifest) ---
@bot.command()
async def gen(ctx, app_id: str):
    status = await ctx.send(f"🛰️ **Connecting to Steam Tools mirror for AppID:** `{app_id}`...")
    try:
        data = download_manifest(app_id)
        
        # Verify it's a real ZIP (PK header) and not an HTML error page
        if data.startswith(b'PK'):
            await status.edit(content=f"✅ **Real Manifest Found!** Uploading for `{app_id}`...")
            await ctx.send(file=discord.File(io.BytesIO(data), filename=f"{app_id}.zip"))
        else:
            raise Exception("Faulty ZIP detected (HTML/Cloudflare block).")
            
    except Exception as e:
        err_msg = str(e)
        await status.edit(content=f"🚨 **Extraction Failed:** `{err_msg}`\n🔧 Initiating Self-Repair...")
        
        # Auto-Repair: Try a simple UA rotation strategy on GitHub
        new_fix = f"import cloudscraper\ndef download_manifest(app_id):\n    s = cloudscraper.create_scraper()\n    r = s.get(f'https://manifest.youngzm.com/api/download/{{app_id}}')\n    return r.content"
        push_to_github(new_fix, "Auto-Fix: Bypass Faulty ZIP")
        await ctx.send("✅ **Code patched on GitHub.** Type `!update` and try again.")

# --- COMMAND: !MODIFY (Talk to AI) ---
@bot.command()
async def modify(ctx, *, prompt: str):
    """Tell the bot to change its own code using AI."""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("⛔ **Permission Denied.** Only the registered owner can re-wire my brain.")

    status = await ctx.send("🧠 **Gemini is thinking...**")
    
    # Get current logic to give AI context
    raw_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{LOGIC_FILE}"
    current_code = requests.get(raw_url, headers={"Authorization": f"token {GITHUB_TOKEN}"}).text

    ai_prompt = f"Current logic code:\n{current_code}\n\nTask: {prompt}\n\nReturn ONLY raw Python code for scraper_logic.py. Do not use markdown blocks."
    
    try:
        # Using Gemini 3 Flash (Free Tier)
        response = ai_client.models.generate_content(model="gemini-2.0-flash", contents=ai_prompt)
        new_code = response.text.strip().replace("```python", "").replace("```", "")
        
        url = push_to_github(new_code, f"AI Mod: {prompt[:30]}")
        await status.edit(content=f"✅ **Brain Modified!** [View Commit]({url})\n👉 **Run `!update` to go live.**")
    except Exception as e:
        await ctx.send(f"❌ AI Modification Error: `{e}`")

# --- COMMAND: !UPDATE (Sync Logic) ---
@bot.command()
async def update(ctx):
    await ctx.send("🔄 **Syncing logic with GitHub...**")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.raw"}
    r = requests.get(f"https://raw.githubusercontent.com/{REPO_NAME}/main/{LOGIC_FILE}", headers=headers)
    if r.status_code == 200:
        exec(r.text, globals())
        await ctx.send("✅ **Logic Synchronized.** You can now use `!gen`.")
    else:
        await ctx.send(f"❌ Failed to sync. GitHub returned `{r.status_code}`")

bot.run(DISCORD_TOKEN)