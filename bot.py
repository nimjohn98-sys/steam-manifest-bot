import discord
from discord.ext import commands
import random
import datetime
import json
import os

# --- 1. CORE ENGINE ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "ultimate_data.json"

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
            "points": 2000, "bank": 0, "multi": 1.0, "shields": 0,
            "hp": 100, "level": 1, "inventory": [], "pets": [],
            "last_daily": None, "last_work": None, "streak": 0
        }
    return db[uid]

# --- 2. DYNAMIC VIEW SYSTEM ---

class GameCenterView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user
        self.category = "Luck"  # Default category

    async def update_message(self, interaction: discord.Interaction, log_msg: str):
        """Ensures only ONE message is ever used by editing the existing one."""
        data = get_user(self.user.id)
        embed = discord.Embed(title="🎮 Sovereign Game Center", color=0x7289da)
        embed.add_field(name="💰 Cash", value=f"{data['points']:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{data['bank']:,}", inline=True)
        embed.add_field(name="🚀 Multi", value=f"x{round(data['multi'], 2)}", inline=True)
        embed.description = f"**Current Category:** {self.category}\n\n**Last Action:**\n> {log_msg}"
        
        # We refresh the view to ensure buttons match the category
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="Choose a Category...",
        options=[
            discord.SelectOption(label="Luck Games", emoji="🎲", value="Luck"),
            discord.SelectOption(label="RPG Actions", emoji="⚔️", value="RPG"),
            discord.SelectOption(label="Assets & Daily", emoji="🎁", value="Assets")
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user.id: return
        self.category = select.values[0]
        # Update buttons visibility based on choice
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = False # Example: could hide/show here
        await self.update_message(interaction, f"Switched to {self.category} mode.")

    # --- BUTTONS ---

    @discord.ui.button(label="🎰 Play / Action", style=discord.ButtonStyle.primary)
    async def play_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        data = get_user(self.user.id)
        log = ""

        if self.category == "Luck":
            # Coin Flip Logic
            win = random.choice([True, False])
            amt = 500
            if win:
                data["points"] += amt
                log = f"🪙 Coinflip: **WON {amt}**!"
            else:
                data["points"] -= (amt // 2)
                log = f"🪙 Coinflip: **LOST {amt//2}**."

        elif self.category == "RPG":
            # Mining Logic
            reward = int(random.randint(100, 400) * data["multi"])
            data["points"] += reward
            log = f"⛏️ Mining: Found ores worth **{reward}**!"

        elif self.category == "Assets":
            # Daily Check
            now = datetime.datetime.now()
            if data["last_daily"]:
                last = datetime.datetime.fromisoformat(data["last_daily"])
                if (now - last).total_seconds() < 86400:
                    log = "⌛ Daily: Already claimed today!"
                else:
                    data["points"] += 1000
                    data["last_daily"] = now.isoformat()
                    log = "🎁 Daily: **+1,000 pts**!"
            else:
                data["points"] += 1000
                data["last_daily"] = now.isoformat()
                log = "🎁 Daily: **+1,000 pts**!"

        save_db(db)
        await self.update_message(interaction, log)

    @discord.ui.button(label="🏦 Bank All", style=discord.ButtonStyle.success)
    async def bank_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        data = get_user(self.user.id)
        total = data["points"]
        data["bank"] += total
        data["points"] = 0
        save_db(db)
        await self.update_message(interaction, f"🏦 Deposited **{total:,}** to bank.")

# --- 3. COMMANDS ---

@bot.command()
async def hub(ctx):
    data = get_user(ctx.author.id)
    embed = discord.Embed(title="🎮 Sovereign Game Center", color=0x7289da)
    embed.add_field(name="💰 Cash", value=f"{data['points']:,}", inline=True)
    embed.add_field(name="🏦 Bank", value=f"{data['bank']:,}", inline=True)
    embed.description = "Select a category from the dropdown to change games!"
    
    await ctx.send(embed=embed, view=GameCenterView(ctx.author))

@bot.event
async def on_ready():
    print(f"🔥 Sovereign Engine Active: {bot.user}")

# --- TOKEN ---
bot.run('PASTE_YOUR_NEW_TOKEN_HERE')
