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
        # Prefix is only for the emergency !sync command
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        self.tree.add_command(minigames_group)
        print(f"✅ Bot initialized as {self.user}")

bot = EconomyBot()
minigames_group = app_commands.Group(name="minigames", description="All ways to play and earn!")

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
        db[uid] = {"points": 100, "messages": 0, "last_daily": None}
    return db[uid]

# ==========================================
# EMERGENCY SYNC COMMAND
# ==========================================
@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    """Type !sync to force Slash Commands to appear immediately."""
    await ctx.send("⏳ Forcing sync...")
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ Synced {len(synced)} commands! Refresh Discord (Ctrl+R) if they don't show.")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

# ==========================================
# BLACKJACK LOGIC
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
# MINIGAMES GROUP
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

@minigames_group.command(name="daily", description="Claim 500 points")
async def daily(interaction: discord.Interaction):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    now = datetime.now()
    if user.get("last_daily") and now < datetime.fromisoformat(user["last_daily"]) + timedelta(days=1):
        return await interaction.response.send_message("⏳ Too early!", ephemeral=True)
    user["points"] += 500
    user["last_daily"] = now.isoformat()
    save_data(DATA_FILE, db)
    await interaction.response.send_message("🎁 +500 points!")

@minigames_group.command(name="koth", description="Overthrow the King (Cost +500 each time)")
async def koth(interaction: discord.Interaction):
    db = get_data(DATA_FILE)
    if "koth" not in db: db["koth"] = {"king": None, "price": 1000}
    uid = str(interaction.user.id)
    price = db["koth"]["price"]
    user = init_user(db, uid)
    if user["points"] < price: return await interaction.response.send_message(f"❌ Need {price} pts.", ephemeral=True)
    user["points"] -= price
    db["koth"]["king"] = uid
    db["koth"]["price"] += 500
    save_data(DATA_FILE, db)
    await interaction.response.send_message(f"👑 {interaction.user.mention} is the NEW KING! (3x Chat Earnings)")

@minigames_group.command(name="lottery", description="Buy a ticket for 100 points")
async def lottery(interaction: discord.Interaction):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    if "lottery" not in db: db["lottery"] = []
    if user["points"] < 100: return await interaction.response.send_message("❌ Need 100 pts.", ephemeral=True)
    user["points"] -= 100
    db["lottery"].append(str(interaction.user.id))
    save_data(DATA_FILE, db)
    pot = len(db["lottery"]) * 100
    await interaction.response.send_message(f"🎟️ Ticket bought! Pot: **{pot}** pts.")

# ==========================================
# SHOP & UTILITY
# ==========================================
@bot.tree.command(name="profile", description="Check stats")
async def profile(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    db = get_data(DATA_FILE)
    user = init_user(db, str(member.id))
    embed = discord.Embed(title=f"👤 {member.display_name}", color=0x3498db)
    embed.add_field(name="Points", value=f"{user['points']:,}")
    if db.get("koth", {}).get("king") == str(member.id): embed.description = "👑 **Current King**"
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setup", description="Admin: Add role to shop")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction, role: discord.Role, price: int):
    cfg = get_data(CONFIG_FILE)
    if "roles" not in cfg: cfg["roles"] = {}
    cfg["roles"][str(role.id)] = {"name": role.name, "price": price}
    save_data(CONFIG_FILE, cfg)
    await interaction.response.send_message(f"✅ Added {role.name} for {price} pts.")

@bot.tree.command(name="shop", description="Browse roles")
async def shop(interaction: discord.Interaction):
    cfg = get_data(CONFIG_FILE)
    embed = discord.Embed(title="🛒 Shop", color=0xf1c40f)
    roles = "".join([f"• <@&{r}>: {i['price']:,} pts\n" for r, i in cfg.get("roles", {}).items()])
    embed.add_field(name="Available Roles", value=roles or "None.")
    await interaction.response.send_message(embed=embed)

# ==========================================
# EVENTS
# ==========================================
@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None: return
    db = get_data(DATA_FILE)
    uid = str(message.author.id)
    user = init_user(db, uid)
    mult = 3 if db.get("koth", {}).get("king") == uid else 1
    user["points"] += (1 * mult)
    user["messages"] += 1
    save_data(DATA_FILE, db)
    await bot.process_commands(message)

bot.run(TOKEN)
