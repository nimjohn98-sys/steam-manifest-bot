import discord
from discord.ext import commands
import random
import datetime
import json
import os

# --- 1. CORE ENGINE ---
intents = discord.Intents.default()
intents.message_content = True  # Required to track message points
bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "sovereign_v3.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

db = load_db()

def get_user(uid):
    uid = str(uid)
    if uid not in db:
        db[uid] = {
            "points": 100, "bank": 0, "multi": 1.0, 
            "last_daily": None, "msg_count": 0
        }
    return db[uid]

# --- 2. MESSAGE TRACKING (POINTS PER MSG) ---

@bot.event
async def on_message(message):
    if message.author.bot: return # Don't give points to bots
    
    # 1 Point Per Message Logic
    data = get_user(message.author.id)
    data["points"] += 1
    data["msg_count"] += 1
    save_db(db)
    
    # Process commands normally
    await bot.process_commands(message)

# --- 3. THE BETTING POPUP ---

class BetModal(discord.ui.Modal, title="💰 Place Your Bet"):
    bet_input = discord.ui.TextInput(
        label="Amount to Bet",
        placeholder="How much you want to risk?",
        min_length=1,
        max_length=10
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.bet_input.value)
            data = get_user(interaction.user.id)
            
            if val <= 0:
                return await interaction.response.send_message("❌ Must bet at least 1 point!", ephemeral=True)
            if val > data["points"]:
                return await interaction.response.send_message(f"❌ You only have {data['points']:,} points!", ephemeral=True)
            
            self.view.current_bet = val
            await self.view.update_message(interaction, f"✅ Bet set to **{val:,}**!")
        except ValueError:
            await interaction.response.send_message("❌ Enter a whole number.", ephemeral=True)

# --- 4. THE MASTER HUB VIEW ---

class SovereignHub(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.user = user
        self.category = "Luck"
        self.current_bet = 10

    async def update_message(self, interaction: discord.Interaction, log: str):
        data = get_user(self.user.id)
        embed = discord.Embed(title="🎮 Sovereign Multi-Game Hub", color=0x5865F2)
        embed.add_field(name="💰 Wallet", value=f"{data['points']:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{data['bank']:,}", inline=True)
        embed.add_field(name="💬 Chat Pts", value=f"{data['msg_count']}", inline=True)
        embed.add_field(name="🎲 Current Bet", value=f"**{self.current_bet:,}**", inline=True)
        embed.description = f"**Category:** {self.category}\n\n**Log:**\n> {log}"
        
        embed.set_footer(text="Earn 1 point for every message you send in chat!")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="Select Game Type...",
        options=[
            discord.SelectOption(label="Casino", emoji="🎰", value="Luck"),
            discord.SelectOption(label="RPG Grinding", emoji="⛏️", value="RPG"),
            discord.SelectOption(label="Account Management", emoji="⚙️", value="Assets")
        ]
    )
    async def change_cat(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user.id: return
        self.category = select.values[0]
        await self.update_message(interaction, f"Mode swapped to {self.category}.")

    @discord.ui.button(label="💰 Change Bet", style=discord.ButtonStyle.secondary)
    async def bet_btn(self, interaction, button):
        if interaction.user.id != self.user.id: return
        await interaction.response.send_modal(BetModal(self))

    @discord.ui.button(label="🕹️ Play Action", style=discord.ButtonStyle.primary)
    async def play_btn(self, interaction, button):
        if interaction.user.id != self.user.id: return
        data = get_user(self.user.id)
        
        if data["points"] < self.current_bet:
            return await interaction.response.send_message("❌ Balance too low for this bet!", ephemeral=True)

        log = ""
        if self.category == "Luck":
            if random.random() > 0.6: # 40% win rate
                reward = self.current_bet * 2
                data["points"] += reward
                log = f"🎰 **WIN!** You doubled your money: **+{reward:,}**"
            else:
                data["points"] -= self.current_bet
                log = f"💀 **LOSE!** Lost your **{self.current_bet:,}** bet."

        elif self.category == "RPG":
            # RPG relies on multipliers
            gain = int(self.current_bet * random.uniform(1.1, 1.8) * data["multi"])
            data["points"] += gain
            log = f"⚔️ **DUNGEON:** Cleared for **{gain:,}** points!"

        elif self.category == "Assets":
            # Check for Daily
            now = datetime.datetime.now()
            if data["last_daily"]:
                last = datetime.datetime.fromisoformat(data["last_daily"])
                if (now - last).total_seconds() < 86400:
                    log = "⌛ **COOLDOWN:** Daily available in a few hours."
                else:
                    data["points"] += 1000
                    data["last_daily"] = now.isoformat()
                    log = "🎁 **CLAIMED:** 1,000 points added!"
            else:
                data["points"] += 1000
                data["last_daily"] = now.isoformat()
                log = "🎁 **CLAIMED:** 1,000 points added!"

        save_db(db)
        await self.update_message(interaction, log)

    @discord.ui.button(label="🏦 Vault All", style=discord.ButtonStyle.success)
    async def vault(self, interaction, button):
        if interaction.user.id != self.user.id: return
        data = get_user(self.user.id)
        amt = data["points"]
        data["bank"] += amt
        data["points"] = 0
        save_db(db)
        await self.update_message(interaction, f"🏦 Moved **{amt:,}** to the vault.")

# --- 5. INITIALIZATION ---

@bot.command()
async def hub(ctx):
    get_user(ctx.author.id) # Ensure profile exists
    embed = discord.Embed(title="🎮 Sovereign Hub", color=0x5865F2)
    view = SovereignHub(ctx.author)
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f"✅ RPG Engine Online: {bot.user}")

bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
