import discord
from discord.ext import commands, tasks
import random
import asyncio
import datetime
import json
import os

# --- 1. CORE ENGINE ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "rpg_city.json"

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
            "points": 2000, "multi": 1.0, "rebirths": 0, "shields": 0,
            "hp": 100, "level": 1, "inventory": [], "streak": 0,
            "last_daily": None, "last_rob": None, "bank": 0
        }
    return db[uid]

# --- 2. THE 20-GAME LOGIC HUB ---

class GameCenter(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    async def check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return False
        return True

    # --- CATEGORY: LUCK (5 GAMES) ---
    @discord.ui.button(label="🎲 Dice Roll", style=discord.ButtonStyle.gray, row=0)
    async def dice(self, interaction, button):
        if not await self.check(interaction): return
        data = get_user(self.user.id)
        if data["points"] < 100: return await interaction.response.send_message("Need 100 pts!", ephemeral=True)
        data["points"] -= 100
        roll = random.randint(1, 6)
        win = 300 if roll > 4 else 0
        data["points"] += win
        save_db(db)
        await interaction.response.send_message(f"🎲 Rolled a {roll}! {'You won 300!' if win else 'Lost!'}", ephemeral=True)

    @discord.ui.button(label="🎰 Slots", style=discord.ButtonStyle.gray, row=0)
    async def slots(self, interaction, button):
        if not await self.check(interaction): return
        data = get_user(self.user.id)
        data["points"] -= 100
        icons = ["🍎", "💎", "7️⃣"]
        res = [random.choice(icons) for _ in range(3)]
        win = 2000 if res[0] == res[1] == res[2] else 0
        data["points"] += win
        save_db(db)
        await interaction.response.send_message(f"{' | '.join(res)} \n{'JACKPOT!' if win else 'Try again.'}", ephemeral=True)

    @discord.ui.button(label="🪙 Coinflip", style=discord.ButtonStyle.gray, row=0)
    async def coin(self, interaction, button):
        if not await self.check(interaction): return
        data = get_user(self.user.id)
        win = random.choice([True, False])
        data["points"] += 200 if win else -100
        save_db(db)
        await interaction.response.send_message(f"🪙 {'Heads! +200' if win else 'Tails! -100'}", ephemeral=True)

    @discord.ui.button(label="📦 Mystery Box", style=discord.ButtonStyle.gray, row=0)
    async def box(self, interaction, button):
        if not await self.check(interaction): return
        data = get_user(self.user.id)
        reward = random.randint(-500, 1000)
        data["points"] += reward
        save_db(db)
        await interaction.response.send_message(f"📦 Box contained: {reward} points!", ephemeral=True)

    @discord.ui.button(label="🎫 Lottery", style=discord.ButtonStyle.gray, row=0)
    async def lotto(self, interaction, button):
        if not await self.check(interaction): return
        win = random.random() < 0.05
        if win:
            get_user(self.user.id)["points"] += 10000
            await interaction.response.send_message("🎫 OMG! You won the 10,000 lottery!", ephemeral=True)
        else:
            get_user(self.user.id)["points"] -= 50
            await interaction.response.send_message("🎫 Not a winner.", ephemeral=True)

    # --- CATEGORY: SKILL/RPG (5 GAMES) ---
    @discord.ui.button(label="⛏️ Mining", style=discord.ButtonStyle.blurple, row=1)
    async def mine(self, interaction, button):
        if not await self.check(interaction): return
        data = get_user(self.user.id)
        reward = random.randint(100, 400)
        data["points"] += reward
        save_db(db)
        await interaction.response.send_message(f"⛏️ Found Iron! +{reward}", ephemeral=True)

    @discord.ui.button(label="🎣 Fishing", style=discord.ButtonStyle.blurple, row=1)
    async def fish(self, interaction, button):
        if not await self.check(interaction): return
        data = get_user(self.user.id)
        fish = random.choice(["🐟", "🐠", "🦈", "👞"])
        val = 500 if fish == "🦈" else 100
        data["points"] += val
        await interaction.response.send_message(f"🎣 Caught {fish}! +{val}", ephemeral=True)

    @discord.ui.button(label="🌲 Hunting", style=discord.ButtonStyle.blurple, row=1)
    async def hunt(self, interaction, button):
        if not await self.check(interaction): return
        res = random.choice(["🦌", "🐇", "🐻"])
        get_user(self.user.id)["points"] += 300
        await interaction.response.send_message(f"🏹 Hunted a {res}! +300", ephemeral=True)

    @discord.ui.button(label="⚔️ Dungeon", style=discord.ButtonStyle.blurple, row=1)
    async def dungeon(self, interaction, button):
        if not await self.check(interaction): return
        win = random.random() > 0.4
        data = get_user(self.user.id)
        if win:
            data["points"] += 1500
            await interaction.response.send_message("⚔️ Cleared the dungeon! +1,500", ephemeral=True)
        else:
            data["hp"] -= 20
            await interaction.response.send_message("💀 Failed! -20 HP.", ephemeral=True)

    @discord.ui.button(label="🧙 Mana Tap", style=discord.ButtonStyle.blurple, row=1)
    async def mana(self, interaction, button):
        if not await self.check(interaction): return
        get_user(self.user.id)["points"] += 50
        await interaction.response.send_message("✨ Generated 50 points from mana!", ephemeral=True)

    # --- CATEGORY: SOCIAL/WAR (5 GAMES) ---
    @discord.ui.button(label="🤺 Duel Bot", style=discord.ButtonStyle.danger, row=2)
    async def duel(self, interaction, button):
        if not await self.check(interaction): return
        win = random.choice([True, False])
        get_user(self.user.id)["points"] += 1000 if win else -500
        await interaction.response.send_message(f"🤺 {'Victory! +1000' if win else 'Defeat! -500'}", ephemeral=True)

    @discord.ui.button(label="💣 Sabotage", style=discord.ButtonStyle.danger, row=2)
    async def boom(self, interaction, button):
        await interaction.response.send_message("Use `!rob @user` to play this!", ephemeral=True)

    @discord.ui.button(label="🕵️ Spy", style=discord.ButtonStyle.danger, row=2)
    async def spy(self, interaction, button):
        await interaction.response.send_message("Use `!bal @user` to spy on balances!", ephemeral=True)

    @discord.ui.button(label="🏴‍☠️ Heist", style=discord.ButtonStyle.danger, row=2)
    async def heist(self, interaction, button):
        if not await self.check(interaction): return
        get_user(self.user.id)["points"] += 2000
        await interaction.response.send_message("🏴‍☠️ Grand Heist success! +2,000", ephemeral=True)

    @discord.ui.button(label="🚔 Prison Break", style=discord.ButtonStyle.danger, row=2)
    async def prison(self, interaction, button):
        if not await self.check(interaction): return
        await interaction.response.send_message("🔓 You escaped! No fine paid.", ephemeral=True)

    # --- CATEGORY: ECONOMY (5 GAMES) ---
    @discord.ui.button(label="💼 Work", style=discord.ButtonStyle.success, row=3)
    async def job(self, interaction, button):
        if not await self.check(interaction): return
        get_user(self.user.id)["points"] += 400
        await interaction.response.send_message("💼 Shift finished! +400", ephemeral=True)

    @discord.ui.button(label="🏦 Bank Interest", style=discord.ButtonStyle.success, row=3)
    async def bank(self, interaction, button):
        if not await self.check(interaction): return
        data = get_user(self.user.id)
        interest = int(data["bank"] * 0.05)
        data["points"] += interest
        await interaction.response.send_message(f"🏦 Interest paid: +{interest}", ephemeral=True)

    @discord.ui.button(label="📈 Day Trade", style=discord.ButtonStyle.success, row=3)
    async def trade(self, interaction, button):
        if not await self.check(interaction): return
        val = random.randint(-1000, 1500)
        get_user(self.user.id)["points"] += val
        await interaction.response.send_message(f"📈 Trade result: {val}", ephemeral=True)

    @discord.ui.button(label="🎁 Daily Reward", style=discord.ButtonStyle.success, row=3)
    async def daily(self, interaction, button):
        if not await self.check(interaction): return
        data = get_user(self.user.id)
        data["points"] += 1000
        data["streak"] += 1
        await interaction.response.send_message(f"🎁 +1000! Streak: {data['streak']}", ephemeral=True)

    @discord.ui.button(label="♻️ Rebirth", style=discord.ButtonStyle.success, row=3)
    async def reb(self, interaction, button):
        if not await self.check(interaction): return
        data = get_user(self.user.id)
        if data["points"] >= 50000:
            data["points"] = 0
            data["rebirths"] += 1
            data["multi"] += 0.5
            await interaction.response.send_message("♻️ REBIRTHED!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Need 50,000 points!", ephemeral=True)

# --- 3. COMMANDS ---

@bot.command()
async def hub(ctx):
    data = get_user(ctx.author.id)
    embed = discord.Embed(title="🎮 The Ultimate Game Center", color=0x00ff00)
    embed.add_field(name="💰 Balance", value=f"{data['points']:,}", inline=True)
    embed.add_field(name="🛡️ Shields", value=data["shields"], inline=True)
    embed.add_field(name="🔥 Streak", value=data["streak"], inline=True)
    embed.description = "Select a game below to play! (20 Games Available)"
    
    await ctx.send(embed=embed, view=GameCenter(ctx.author))

@bot.command()
async def rob(ctx, target: discord.Member):
    atk = get_user(ctx.author.id)
    vic = get_user(target.id)
    if vic["shields"] > 0:
        vic["shields"] -= 1
        return await ctx.send("🛡️ Shield blocked!")
    
    stolen = int(vic["points"] * 0.2)
    vic["points"] -= stolen
    atk["points"] += stolen
    save_db(db)
    await ctx.send(f"🥷 Stole {stolen}!")

@bot.event
async def on_ready():
    print(f"🔥 System Online: {bot.user}")

# --- TOKEN ---
bot.run('MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg')
