import discord
from discord.ext import commands
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION - USE YOUR ACTUAL TOKEN HERE
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
DATA_FILE = "points_database.json"

class EconomyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # MUST BE ON IN DEV PORTAL
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def on_ready(self):
        print(f'✅ Bot is ONLINE as {self.user}')
        print('>> Type !minigames in Discord to start.')

bot = EconomyBot()

# ==========================================
# DATABASE HELPERS
# ==========================================
def get_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def init_user(db, uid):
    if uid not in db:
        db[uid] = {"points": 1000, "messages": 0, "last_daily": None, "last_work": None}
    return db[uid]

# ==========================================
# BUTTON-BASED GAMES & MENUS
# ==========================================

# --- Blackjack View ---
class BlackjackView(discord.ui.View):
    def __init__(self, ctx, uid, bet):
        super().__init__(timeout=60)
        self.ctx, self.uid, self.bet = ctx, str(uid), bet
        self.deck = [{'v': v, 's': s} for v in ['2','3','4','5','6','7','8','9','10','J','Q','K','A'] for s in ['♠️','♥️','♦️','♣️']]
        random.shuffle(self.deck)
        self.p_hand = [self.deck.pop(), self.deck.pop()]
        self.d_hand = [self.deck.pop(), self.deck.pop()]

    def get_val(self, hand):
        v, aces = 0, 0
        for c in hand:
            if c['v'] in ['J','Q','K']: v += 10
            elif c['v'] == 'A': v += 11; aces += 1
            else: v += int(c['v'])
        while v > 21 and aces: v -= 10; aces -= 1
        return v

    def embed(self, done=False):
        pv, dv = self.get_val(self.p_hand), self.get_val(self.d_hand)
        e = discord.Embed(title="🃏 Blackjack", color=0x2ecc71)
        e.add_field(name=f"You ({pv})", value=" ".join([f"[{c['v']}{c['s']}]" for c in self.p_hand]))
        if done: e.add_field(name=f"Dealer ({dv})", value=" ".join([f"[{c['v']}{c['s']}]" for c in self.d_hand]))
        else: e.add_field(name="Dealer (?)", value=f"[{self.d_hand[0]['v']}{self.d_hand[0]['s']}] [❓]")
        return e

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple)
    async def hit(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        self.p_hand.append(self.deck.pop())
        if self.get_val(self.p_hand) > 21: await self.end(interaction, "BUST! You lost.")
        else: await interaction.response.edit_message(embed=self.embed())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        while self.get_val(self.d_hand) < 17: self.d_hand.append(self.deck.pop())
        pv, dv = self.get_val(self.p_hand), self.get_val(self.d_hand)
        res = "YOU WIN!" if dv > 21 or pv > dv else ("DEALER WINS." if pv < dv else "PUSH.")
        await self.end(interaction, res)

    async def end(self, interaction, res):
        db = get_data(); user = init_user(db, self.uid)
        if "WIN" in res: user["points"] += (self.bet * 2)
        elif "PUSH" in res: user["points"] += self.bet
        save_data(db)
        await interaction.response.edit_message(content=f"**{res}**", embed=self.embed(True), view=None)

# --- The Main Hub ---
class GameHub(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx

    @discord.ui.button(label="Blackjack", style=discord.ButtonStyle.green, emoji="🃏", row=0)
    async def bj(self, interaction: discord.Interaction, btn: discord.ui.Button):
        db = get_data(); user = init_user(db, str(interaction.user.id))
        if user["points"] < 100: return await interaction.response.send_message("Need 100 pts!", ephemeral=True)
        user["points"] -= 100; save_data(db)
        v = BlackjackView(self.ctx, interaction.user.id, 100)
        await interaction.response.send_message(embed=v.embed(), view=v)

    @discord.ui.button(label="Slots", style=discord.ButtonStyle.blurple, emoji="🎰", row=0)
    async def slots(self, interaction: discord.Interaction, btn: discord.ui.Button):
        db = get_data(); user = init_user(db, str(interaction.user.id))
        if user["points"] < 50: return await interaction.response.send_message("Need 50 pts!", ephemeral=True)
        user["points"] -= 50
        icons = ["🍒", "🍋", "🍇", "💎"]
        res = [random.choice(icons) for _ in range(3)]
        win = 0
        if res[0] == res[1] == res[2]: win = 500 if res[0]=="💎" else 250
        elif res[0] == res[1] or res[1] == res[2]: win = 75
        user["points"] += win; save_data(db)
        await interaction.response.send_message(f"🎰 | {' | '.join(res)} | 🎰\n{'Won ' + str(win) if win > 0 else 'Lost!'}")

    @discord.ui.button(label="Coinflip", style=discord.ButtonStyle.gray, emoji="🪙", row=0)
    async def coin(self, interaction: discord.Interaction, btn: discord.ui.Button):
        db = get_data(); user = init_user(db, str(interaction.user.id))
        if user["points"] < 50: return await interaction.response.send_message("Need 50 pts!", ephemeral=True)
        user["points"] -= 50
        if random.random() > 0.5: user["points"] += 100; msg = "Heads! You doubled it."
        else: msg = "Tails... you lost."
        save_data(db); await interaction.response.send_message(msg)

    @discord.ui.button(label="Daily Bonus", style=discord.ButtonStyle.primary, emoji="🎁", row=1)
    async def daily(self, interaction: discord.Interaction, btn: discord.ui.Button):
        db = get_data(); user = init_user(db, str(interaction.user.id))
        now = datetime.now()
        if user.get("last_daily") and now < datetime.fromisoformat(user["last_daily"]) + timedelta(days=1):
            return await interaction.response.send_message("⏳ Come back tomorrow!", ephemeral=True)
        user["points"] += 500; user["last_daily"] = now.isoformat(); save_data(db)
        await interaction.response.send_message("✅ +500 points claimed!")

# ==========================================
# COMMANDS
# ==========================================

@bot.command()
async def minigames(ctx):
    """The hub for all games"""
    embed = discord.Embed(title="🎮 Economy Game Center", description="Click a button below to play a game!\n\n• Blackjack: 100 pts\n• Slots: 50 pts\n• Coinflip: 50 pts", color=0x3498db)
    await ctx.send(embed=embed, view=GameHub(ctx))

@bot.command()
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author
    db = get_data(); user = init_user(db, str(member.id))
    await ctx.send(f"👤 **{member.display_name}** | Points: **{user['points']:,}**")

@bot.command()
@commands.has_permissions(administrator=True)
async def admin_give(ctx, member: discord.Member, amount: int):
    db = get_data(); user = init_user(db, str(member.id))
    user["points"] += amount; save_data(db)
    await ctx.send(f"✅ Added {amount:,} to {member.mention}")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    db = get_data(); user = init_user(db, str(message.author.id))
    user["points"] += 1; save_data(db)
    await bot.process_commands(message) # CRITICAL for ! commands

bot.run(TOKEN)
