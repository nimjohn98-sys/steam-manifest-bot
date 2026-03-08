import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
DATA_FILE = "points_database.json"
CONFIG_FILE = "server_config.json"

class EconomyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.manage_roles = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Register the Minigames Group
        self.tree.add_command(minigames_group)
        await self.tree.sync()
        print(f"✅ Economy Bot Online | {self.user}")

bot = EconomyBot()
minigames_group = app_commands.Group(name="minigames", description="Earning and gambling commands")

# ==========================================
# DATABASE HELPERS
# ==========================================
def get_data(file):
    if not os.path.exists(file): return {}
    with open(file, "r") as f:
        try: return json.load(f)
        except: return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def init_user(db, uid):
    if uid not in db:
        db[uid] = {"points": 100, "messages": 0, "last_daily": None, "last_work": None}
    return db[uid]

# ==========================================
# EVENTS (POINT EARNING)
# ==========================================
@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None: return
    
    db = get_data(DATA_FILE)
    uid = str(message.author.id)
    user = init_user(db, uid)
    
    # 3x Points for the King of the Hill
    multiplier = 3 if db.get("koth", {}).get("king") == uid else 1
    user["points"] += (1 * multiplier)
    user["messages"] += 1
    
    save_data(DATA_FILE, db)
    await bot.process_commands(message)

# ==========================================
# BLACKJACK CLASSES
# ==========================================
def calc_hand(hand):
    val, aces = 0, 0
    for c in hand:
        if c['v'] in ['J', 'Q', 'K']: val += 10
        elif c['v'] == 'A': val += 11; aces += 1
        else: val += int(c['v'])
    while val > 21 and aces: val -= 10; aces -= 1
    return val

class BlackjackView(discord.ui.View):
    def __init__(self, interaction, uid, bet):
        super().__init__(timeout=60)
        self.interaction, self.uid, self.bet = interaction, str(uid), bet
        suits, vals = ['♠️', '♥️', '♦️', '♣️'], ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        self.deck = [{'v': v, 's': s} for v in vals for s in suits]
        random.shuffle(self.deck)
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]

    def get_embed(self, done=False):
        p_val = calc_hand(self.player_hand)
        d_val = calc_hand(self.dealer_hand)
        embed = discord.Embed(title="🃏 Blackjack", color=0x2ecc71)
        embed.add_field(name=f"You ({p_val})", value=" ".join([f"[{c['v']}{c['s']}]" for c in self.player_hand]))
        if done:
            embed.add_field(name=f"Dealer ({d_val})", value=" ".join([f"[{c['v']}{c['s']}]" for c in self.dealer_hand]))
        else:
            embed.add_field(name="Dealer (?)", value=f"[{self.dealer_hand[0]['v']}{self.dealer_hand[0]['s']}] [❓]")
        return embed

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        self.player_hand.append(self.deck.pop())
        if calc_hand(self.player_hand) > 21: await self.finish(interaction, "BUST! You lost.")
        else: await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        while calc_hand(self.dealer_hand) < 17: self.dealer_hand.append(self.deck.pop())
        p, d = calc_hand(self.player_hand), calc_hand(self.dealer_hand)
        if d > 21 or p > d: res = "YOU WIN!"
        elif p < d: res = "DEALER WINS."
        else: res = "PUSH (Tie)."
        await self.finish(interaction, res)

    async def finish(self, interaction, res):
        db = get_data(DATA_FILE)
        if "WIN" in res: db[self.uid]["points"] += (self.bet * 2)
        elif "PUSH" in res: db[self.uid]["points"] += self.bet
        save_data(DATA_FILE, db)
        self.stop()
        await interaction.response.edit_message(content=f"**{res}**", embed=self.get_embed(True), view=None)

# ==========================================
# MINIGAMES GROUP COMMANDS
# ==========================================

@minigames_group.command(name="blackjack", description="Play Blackjack")
async def bj(interaction: discord.Interaction, bet: int):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    if bet <= 0 or user["points"] < bet: return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)
    user["points"] -= bet
    save_data(DATA_FILE, db)
    view = BlackjackView(interaction, interaction.user.id, bet)
    await interaction.response.send_message(embed=view.get_embed(), view=view)

@minigames_group.command(name="daily", description="Claim 500 daily points")
async def daily(interaction: discord.Interaction):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    now = datetime.now()
    if user["last_daily"] and now < datetime.fromisoformat(user["last_daily"]) + timedelta(days=1):
        return await interaction.response.send_message("⏳ Come back tomorrow!", ephemeral=True)
    user["points"] += 500
    user["last_daily"] = now.isoformat()
    save_data(DATA_FILE, db)
    await interaction.response.send_message("🎁 You claimed **500** points!")

@minigames_group.command(name="koth", description="Overthrow the King for 3x earning")
async def koth(interaction: discord.Interaction):
    db = get_data(DATA_FILE)
    if "koth" not in db: db["koth"] = {"king": None, "price": 1000}
    uid = str(interaction.user.id)
    price = db["koth"]["price"]
    user = init_user(db, uid)
    
    if uid == db["koth"]["king"]: return await interaction.response.send_message("👑 You are already King!", ephemeral=True)
    if user["points"] < price: return await interaction.response.send_message(f"❌ You need {price} points.", ephemeral=True)
    
    user["points"] -= price
    db["koth"]["king"] = uid
    db["koth"]["price"] += 500
    save_data(DATA_FILE, db)
    await interaction.response.send_message(f"👑 **{interaction.user.mention} IS THE NEW KING!** (Earnings: 3x)")

@minigames_group.command(name="rps", description="Rock Paper Scissors")
@app_commands.choices(choice=[
    app_commands.Choice(name="Rock", value="rock"),
    app_commands.Choice(name="Paper", value="paper"),
    app_commands.Choice(name="Scissors", value="scissors")
])
async def rps(interaction: discord.Interaction, choice: app_commands.Choice[str], bet: int):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    if bet <= 0 or user["points"] < bet: return await interaction.response.send_message("❌ Bad bet.", ephemeral=True)
    
    bot_c = random.choice(["rock", "paper", "scissors"])
    user["points"] -= bet
    if choice.value == bot_c: user["points"] += bet; msg = "Tie!"
    elif (choice.value == "rock" and bot_c == "scissors") or (choice.value == "paper" and bot_c == "rock") or (choice.value == "scissors" and bot_c == "paper"):
        user["points"] += bet * 2; msg = "You won!"
    else: msg = "You lost."
    save_data(DATA_FILE, db)
    await interaction.response.send_message(f"I chose {bot_c}. **{msg}**")

# ==========================================
# SHOP & PROFILE
# ==========================================

@bot.tree.command(name="profile", description="View stats")
async def profile(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    db = get_data(DATA_FILE)
    user = init_user(db, str(member.id))
    embed = discord.Embed(title=f"👤 {member.display_name}", color=0x3498db)
    embed.add_field(name="🪙 Points", value=f"{user['points']:,}")
    embed.add_field(name="📩 Messages", value=f"{user['messages']:,}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="shop", description="View the shop")
async def shop(interaction: discord.Interaction):
    cfg = get_data(CONFIG_FILE)
    embed = discord.Embed(title="🛒 Server Shop", color=0xf1c40f)
    roles = "".join([f"• <@&{r}>: **{i['price']:,}** pts\n" for r, i in cfg.get("roles", {}).items()])
    embed.add_field(name="Roles", value=roles or "None.")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setup", description="Admin Only: Set shop prices")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction, role: discord.Role, price: int):
    cfg = get_data(CONFIG_FILE)
    if "roles" not in cfg: cfg["roles"] = {}
    cfg["roles"][str(role.id)] = {"name": role.name, "price": price}
    save_data(CONFIG_FILE, cfg)
    await interaction.response.send_message(f"✅ Added {role.name} to shop.")

bot.run(TOKEN)
