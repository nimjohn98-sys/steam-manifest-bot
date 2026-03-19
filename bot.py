import discord
from discord.ext import commands
import aiohttp
import asyncio
import os
import subprocess
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Optional

# Bot configuration
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.G3LaxK.fZlnILy97sdYpcPdHM3iMilnt_htym2axHyeT8"  # Replace with your bot token
PREFIX = "!"

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Steamtools path - will be auto-detected
STEAMTOOLS_PATH = None

def find_steamtools():
    """Find steamtools executable"""
    global STEAMTOOLS_PATH
    
    # Common locations for steamtools
    possible_paths = [
        "/usr/local/bin/steamtools",
        "/opt/homebrew/bin/steamtools",  # macOS
        "/usr/bin/steamtools",
        "./steamtools",
        "../steamtools",
        os.path.expanduser("~/steamtools"),
        os.path.expanduser("~/.local/bin/steamtools")
    ]
    
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            STEAMTOOLS_PATH = path
            return path
    
    # Try to find in PATH
    try:
        result = subprocess.run(["which", "steamtools"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            STEAMTOOLS_PATH = result.stdout.strip()
            return STEAMTOOLS_PATH
    except:
        pass
        
    return None

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Check for steamtools on startup
    steamtools_path = find_steamtools()
    if steamtools_path:
        print(f"✅ Steamtools found at: {steamtools_path}")
    else:
        print("⚠️  Steamtools not found. Please install it:")
        print("   Visit: https://steamtools.net/download.html")
        print("   Or run: curl -fsSL https://steamtools.net/install.sh | sh")

@bot.command(name='gen')
async def generate_manifest(ctx, appid: str):
    """
    Generate Steam manifest for given AppID
    Usage: !gen <appid>
    """
    # Validate appid is numeric
    if not appid.isdigit():
        await ctx.send("❌ Please provide a valid numeric AppID")
        return
    
    # Check if steamtools is available
    steamtools_path = find_steamtools()
    if not steamtools_path:
        await ctx.send("""
❌ **Steamtools not found!**

To use this bot, you need to install steamtools:

**Linux/macOS:**
```bash
curl -fsSL https://steamtools.net/install.sh | sh
```

**Windows:**
Download from: https://steamtools.net/download.html

After installation, please restart the bot.
""")
        return
    
    await ctx.send(f"🔄 Generating manifest for AppID {appid}...")
    
    try:
        # Create temporary directory for our work
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manifest_dir = temp_path / "manifest"
            manifest_dir.mkdir()
            
            # Generate manifest using steamtools
            # Based on steamtools documentation, we can use:
            # steamtools manifest <appid> <output_directory>
            print(f"Running: {steamtools_path} manifest {appid} {manifest_dir}")
            
            result = subprocess.run([
                steamtools_path, 
                "manifest", 
                appid, 
                str(manifest_dir)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                await ctx.send(f"❌ Failed to generate manifest:\n```{error_msg}```")
                return
            
            # Check if manifest was generated
            manifest_files = list(manifest_dir.glob("*.acf"))
            if not manifest_files:
                await ctx.send(f"❌ No manifest files generated for AppID {appid}. The AppID might be invalid or the game might not be owned.")
                return
            
            # Create zip file
            zip_path = temp_path / f"manifest_{appid}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for manifest_file in manifest_dir.iterdir():
                    if manifest_file.is_file():
                        zipf.write(manifest_file, manifest_file.name)
            
            # Check if zip is too large for Discord (limit is ~25MB)
            if zip_path.stat().st_size > 25 * 1024 * 1024:
                await ctx.send(f"❌ Manifest zip is too large (>25MB) to send via Discord.")
                return
            
            # Send the zip file
            await ctx.send(
                f"📦 Here's the manifest for AppID {appid}:",
                file=discord.File(zip_path)
            )
            
    except subprocess.TimeoutExpired:
        await ctx.send("❌ Manifest generation timed out (took too long).")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")
        print(f"Error in !gen command: {e}")

@bot.command(name='helpmanifest')
async def help_manifest(ctx):
    """Show help for manifest commands"""
    embed = discord.Embed(
        title="📋 Manifest Bot Help",
        description="Commands for generating Steam manifest files",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="!gen <appid>",
        value="Generate manifest zip for the given Steam AppID\nExample: `!gen 730` for CS:GO\nRequires steamtools to be installed",
        inline=False
    )
    embed.add_field(
        name="!helpmanifest",
        value="Show this help message",
        inline=False
    )
    embed.add_field(
        name="!steamtools",
        value="Check steamtools installation status",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='steamtools')
async def check_steamtools(ctx):
    """Check steamtools installation"""
    steamtools_path = find_steamtools()
    if steamtools_path:
        # Try to get version
        try:
            result = subprocess.run([steamtools_path, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            version = result.stdout.strip() if result.returncode == 0 else "Unknown"
            await ctx.send(f"✅ Steamtools found at: `{steamtools_path}`\nVersion: {version}")
        except:
            await ctx.send(f"✅ Steamtools found at: `{steamtools_path}`")
    else:
        await ctx.send("""
❌ Steamtools not found.

To install:
**Linux/macOS:**
```bash
curl -fsSL https://steamtools.net/install.sh | sh
```

**Windows:**
Download from: https://steamtools.net/download.html
""")

# Run the bot
if __name__ == "__main__":
    # You'll need to set your Discord bot token as an environment variable
    # or replace TOKEN above with your actual bot token
    token = os.getenv('DISCORD_BOT_TOKEN', TOKEN)
    if token == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("⚠️  WARNING: Please set your Discord bot token!")
        print("You can:")
        print("1. Replace TOKEN in the code with your bot token")
        print("2. Set environment variable DISCORD_BOT_TOKEN")
        print("3. Get a token from https://discord.com/developers/applications")
    else:
        bot.run(token)
