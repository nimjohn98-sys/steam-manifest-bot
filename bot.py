import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import requests
from DrissionPage import ChromiumPage, ChromiumOptions

# --- CONFIGURATION ---
TOKEN = "MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg"
TARGET_SITE = "https://manifest.youngzm.com/"
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # This syncs your slash commands to Discord's servers
        await self.tree.sync()
        print(f"✅ Slash commands synced for {self.user}")

bot = MyBot()

# --- THE INFO SLASH COMMAND ---
@bot.tree.command(name="info", description="Learn how to find a Steam AppID and use this bot")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 How to use Manifest Gen",
        description="To generate a manifest, I need a **Steam AppID**.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="1. How to find the AppID",
        value=(
            "• **The URL Method:** Go to the game's Steam Store page. The number in the URL "
            "(`store.steampowered.com/app/XXXXXX/`) is the AppID.\n"
            "• **Google Method:** Search for `[Game Name] steam appid`.\n"
            "• **SteamDB:** Search on [SteamDB.info](https://steamdb.info)."
        ),
        inline=False
    )
    embed.add_field(
        name="2. How to use me",
        value="Type `/gen` and then either the **Game Name** or the **AppID**.",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

# --- THE GENERATE SLASH COMMAND ---
@bot.tree.command(name="gen", description="Generate a Steam manifest file")
@app_commands.describe(query="The name of the game or the Steam AppID")
async def gen(interaction: discord.Interaction, query: str):
    # We defer the response because browser automation takes longer than 3 seconds
    await interaction.response.defer()
    
    # [Insert your existing processing logic here - calling process_request(query)]
    # For now, a placeholder response:
    await interaction.followup.send(f"⚙️ Starting generation for: `{query}`...")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
