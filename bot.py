import discord
from discord.ext import commands
import requests
import cloudscraper
import io
from github import Github  # pip install PyGithub

# --- CONFIGURATION ---
DISCORD_TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
GITHUB_TOKEN = "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"
REPO_NAME = "nimjohn98-sys/steam-manifest-bot"
LOGIC_FILE_PATH = "scraper_logic.py"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- NOTIFYING GITHUB LOGIC ---
def update_github_code(new_code):
    """Updates GitHub and returns the commit URL."""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(LOGIC_FILE_PATH, ref="main")
    
    # Update the file
    commit_result = repo.update_file(
        contents.path, 
        "🛠️ Automated Self-Healing Fix", 
        new_code, 
        contents.sha, 
        branch="main"
    )
    return commit_result['commit'].html_url

# Placeholder logic
def download_manifest(app_id):
    raise Exception("403 Forbidden: Cloudflare Block Detected")

@bot.command()
async def gen(ctx, app_id: str):
    try:
        data = download_manifest(app_id)
        await ctx.send(file=discord.File(io.BytesIO(data), filename=f"{app_id}.zip"))
    except Exception as e:
        error_msg = str(e)
        
        # 1. NOTIFY: Start of repair
        status_msg = await ctx.send(f"⚠️ **Error Detected:** `{error_msg}`\n🔧 **Initiating Self-Repair...**")
        
        # 2. ANALYSIS: (Simplified for this example)
        if "403" in error_msg:
            await status_msg.edit(content=f"🔍 **Analyzing:** Detected a 403 Block. Rewriting `scraper_logic.py` with new headers...")
            
            new_logic = f"""
import cloudscraper
def download_manifest(app_id):
    # Auto-generated fix for 403
    scraper = cloudscraper.create_scraper(browser={{'browser': 'chrome', 'platform': 'windows'}})
    url = f"https://manifest.youngzm.com/api/download/{{app_id}}"
    r = scraper.get(url)
    return r.content
"""
            try:
                # 3. NOTIFY: Modifying GitHub
                await status_msg.edit(content="🛰️ **Connecting to GitHub API...**")
                commit_url = update_github_code(new_logic)
                
                # 4. NOTIFY: Success
                embed = discord.Embed(
                    title="✅ Code Modified Successfully",
                    description=f"I have rewritten the scraping logic to bypass the 403 error.",
                    color=discord.Color.green()
                )
                embed.add_field(name="Commit Details", value=f"[View on GitHub]({commit_url})")
                embed.set_footer(text="Type !update to apply these changes to the bot.")
                await ctx.send(embed=embed)
                
            except Exception as github_err:
                await ctx.send(f"❌ **Failed to modify code:** `{github_err}`")

@bot.command()
async def update(ctx):
    await ctx.send("🔄 **Syncing code...**")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.raw"}
    r = requests.get(f"https://raw.githubusercontent.com/{REPO_NAME}/main/{LOGIC_FILE_PATH}", headers=headers)
    if r.status_code == 200:
        exec(r.text, globals())
        await ctx.send("✅ **Brain updated!** The repair is now live.")

bot.run(DISCORD_TOKEN)
