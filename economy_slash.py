import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
DATA_FILE = "points_database.json"

class EconomyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # This syncs the slash commands to your server
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = EconomyBot()

# --- DATABASE HELPERS ---
def load_db():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def init_user(data, user_id):
    if user_id not in data:
        data[user_id] = {"points": 100, "messages": 0, "last_daily": None}
    return data[user_id]

# --- POINTS FOR CHATTING ---
@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None: return
    data = load_db()
    user = init_user(data, str(message.author.id))
    user["points"] += 1
    user["messages"] += 1
    save_db(data)
    await bot.process_commands(message)

# --- SLASH COMMANDS ---

@bot.tree.command(name="points", description="Check your point balance")
async def points(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_db()
    user = init_user(data, str(member.id))
    await interaction.response.send_message(f"🪙 **{member.display_name}** has **{user['points']}** points!")

@bot.tree.command(name="daily", description="Claim your 500 daily points")
async def daily(interaction: discord.Interaction):
    data = load_db()
    user = init_user(data, str(interaction.user.id))
    now = datetime.now()
    
    last = user.get("last_daily")
    if last and now < datetime.fromisoformat(last) + timedelta(days=1):
        return await interaction.response.send_message("⏳ Try again tomorrow!", ephemeral=True)

    user["points"] += 500
    user["last_daily"] = now.isoformat()
    save_db(data)
    await interaction.response.send_message(f"🎁 {interaction.user.mention}, you claimed **500** points!")

@bot.tree.command(name="rps", description="Play Rock Paper Scissors for points")
@app_commands.describe(choice="Choose your weapon", bet="Amount to bet")
@app_commands.choices(choice=[
    app_commands.Choice(name="Rock", value="rock"),
    app_commands.Choice(name="Paper", value="paper"),
    app_commands.Choice(name="Scissors", value="scissors"),
])
async def rps(interaction: discord.Interaction, choice: app_commands.Choice[str], bet: int):
    data = load_db()
    user = init_user(data, str(interaction.user.id))
    
    if bet <= 0 or user["points"] < bet:
        return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)

    bot_choice = random.choice(["rock", "paper", "scissors"])
    user["points"] -= bet
    
    if choice.value == bot_choice:
        user["points"] += bet
        msg = "🤝 It's a tie!"
    elif (choice.value == "rock" and bot_choice == "scissors") or \
         (choice.value == "paper" and bot_choice == "rock") or \
         (choice.value == "scissors" and bot_choice == "paper"):
        user["points"] += bet * 2
        msg = f"🏆 You won **{bet * 2}** points!"
    else:
        msg = f"💀 I chose {bot_choice}. You lost."

    save_db(data)
    await interaction.response.send_message(f"You: **{choice.name}** | Me: **{bot_choice}**\n{msg}")

@bot.tree.command(name="roulette", description="Bet on a color")
@app_commands.choices(color=[
    app_commands.Choice(name="🔴 Red (2x)", value="red"),
    app_commands.Choice(name="⚫ Black (2x)", value="black"),
    app_commands.Choice(name="🟢 Green (35x)", value="green"),
])
async def roulette(interaction: discord.Interaction, color: app_commands.Choice[str], bet: int):
    data = load_db()
    user = init_user(data, str(interaction.user.id))
    if bet <= 0 or user["points"] < bet:
        return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)

    user["points"] -= bet
    outcome = random.choices(["red", "black", "green"], weights=[18, 18, 1], k=1)[0]
    
    if color.value == outcome:
        mult = 35 if outcome == "green" else 2
        user["points"] += bet * mult
        msg = f"🎡 Landed on **{outcome}**! Won **{bet*mult}** pts!"
    else:
        msg = f"🎡 Landed on **{outcome}**. Lost your bet."

    save_db(data)
    await interaction.response.send_message(msg)

bot.run(TOKEN)
