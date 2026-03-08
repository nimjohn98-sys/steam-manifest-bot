import discord
from discord.ext import commands
import random
import datetime
import json
import os

# --- 1. ENGINE SETUP ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "sovereign_pro.json"

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
        db[uid] = {"points": 2000, "bank": 0, "multi": 1.0, "last_daily": None}
    return db[uid]

# --- 2. THE BETTING POPUP (MODAL) ---

class BetModal(discord.ui.Modal, title="💰 Place Your Bet"):
    bet_input = discord.ui.TextInput(
        label="Amount to Bet",
        placeholder="Enter a number...",
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
                return await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
            if val > data["points"]:
                return await interaction.response.send_message(f"❌ You only have {data['points']:,} points!", ephemeral=True)
            
            self.view.current_bet = val
            await self.view.update_message(interaction, f"✅ Bet set to **{val:,}**!")
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number.", ephemeral=True)

# --- 3. THE DYNAMIC HUB VIEW ---

class SovereignHub(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.user = user
        self.category = "Luck"
        self.current_bet = 100 # Default bet

    async def update_message(self, interaction: discord.Interaction, log: str):
        data = get_user(self.user.id)
        embed = discord.Embed(title="🎮 Sovereign Hub", color=0x2f3136)
        embed.add_field(name="💰 Wallet", value=f"{data['points']:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{data['bank']:,}", inline=True)
        embed.add_field(name="🎲 Current Bet", value=f"**{self.current_bet:,}**", inline=True)
        embed.description = f"**Category:** {self.category}\n\n**System Log:**\n> {log}"
        
        # Set footer to show help
        embed.set_footer(text="Banked points are safe from robbery!")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="Choose a Game Category...",
        options=[
            discord.SelectOption(label="Luck (Casino)", emoji="🎰", value="Luck"),
            discord.SelectOption(label="RPG (Grind)", emoji="⛏️", value="RPG"),
            discord.SelectOption(label="Daily & Bank", emoji="🏦", value="Assets")
        ]
    )
    async def select_cat(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user.id: return
        self.category = select.values[0]
        await self.update_message(interaction, f"Switched to {self.category}.")

    @discord.ui.button(label="💰 Change Bet", style=discord.ButtonStyle.gray)
    async def set_bet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        await interaction.response.send_modal(BetModal(self))

    @discord.ui.button(label="🚀 PLAY", style=discord.ButtonStyle.primary)
    async def play_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        data = get_user(self.user.id)
        
        # Double check they still have the money
        if data["points"] < self.current_bet:
            return await interaction.response.send_message("❌ You no longer have enough points for this bet!", ephemeral=True)

        log = ""
        if self.category == "Luck":
            win = random.random() > 0.55 # 45% win rate
            if win:
                reward = self.current_bet * 2
                data["points"] += reward
                log = f"🎰 **JACKPOT!** You won **{reward:,}**!"
            else:
                data["points"] -= self.current_bet
                log = f"💀 **LOSE!** You lost your bet of **{self.current_bet:,}**."

        elif self.category == "RPG":
            # Mining uses bet as "Gear Quality"
            success = random.random() > 0.2
            if success:
                gain = int(self.current_bet * random.uniform(1.2, 2.0))
                data["points"] += gain
                log = f"⛏️ **MINED!** Your gear found **{gain:,}** worth of gold!"
            else:
                data["points"] -= self.current_bet
                log = f"🛠️ **BROKEN!** Your tools broke. Lost **{self.current_bet:,}**."

        elif self.category == "Assets":
            # Daily doesn't use bets
            now = datetime.datetime.now()
            if data["last_daily"]:
                last = datetime.datetime.fromisoformat(data["last_daily"])
                if (now - last).total_seconds() < 86400:
                    log = "⌛ **WAIT!** Daily is on cooldown."
                else:
                    data["points"] += 2000
                    data["last_daily"] = now.isoformat()
                    log = "🎁 **DAILY!** +2,000 pts!"
            else:
                data["points"] += 2000
                data["last_daily"] = now.isoformat()
                log = "🎁 **DAILY!** +2,000 pts!"

        save_db(db)
        await self.update_message(interaction, log)

    @discord.ui.button(label="🏦 Bank All", style=discord.ButtonStyle.success)
    async def bank_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        data = get_user(self.user.id)
        amt = data["points"]
        data["bank"] += amt
        data["points"] = 0
        save_db(db)
        await self.update_message(interaction, f"🏦 Secured **{amt:,}** in the vault.")

# --- 4. RUN ---

@bot.command()
async def hub(ctx):
    await ctx.send("🌍 Loading Sovereign Hub...", delete_after=1)
    embed = discord.Embed(title="🎮 Sovereign Hub", color=0x2f3136)
    view = SovereignHub(ctx.author)
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f"🔥 Online: {bot.user}")

bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
