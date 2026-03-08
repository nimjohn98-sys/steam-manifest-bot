import discord
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
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def on_ready(self):
        print(f'🚀 Prefix Bot Online: {self.user}')
        print('Commands: !minigames, !profile, !shop, !admin_give')

bot = EconomyBot()

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
        db[uid] = {"points": 1000, "messages": 0, "last_daily": None, "last_work": None}
    return db[uid]

# ==========================================
# GAME LOGIC & VIEWS
# ==========================================

# --- Blackjack View ---
def calc_hand(hand):
    val, aces = 0, 0
    for c in hand:
        if c['v'] in ['J', 'Q', 'K']: val += 10
        elif c['v'] == 'A': val += 11; aces += 1
        else: val += int(c['v'])
    while val > 21 and aces: val -= 10; aces -= 1
    return val

class BlackjackView(discord.ui.View):
    def __init__(self, ctx, uid, bet):
        super().__init__(timeout=60)
        self.ctx, self.uid, self.bet = ctx, str(uid), bet
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

# --- Main Menu View ---
class MinigameMenu(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx

    @discord.ui.button(label="Blackjack (100)", style=discord.ButtonStyle.green, emoji="🃏")
    async def bj_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = get_data(DATA_FILE); user = init_user(db, str(interaction.user.id))
        if user["points"] < 100: return await interaction.response.send_message("Need 100 pts!", ephemeral=True)
        user["points"] -= 100; save_data(DATA_FILE, db)
        view = BlackjackView(self.ctx, interaction.user.id, 100)
        await interaction.response.send_message(embed=view.get_embed(), view=view)

    @discord.ui.button(label="Slots (50)", style=discord.ButtonStyle.blurple, emoji="🎰")
    async def slots_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = get_data(DATA_FILE); user = init_user(db, str(interaction.user.id))
        if user["points"] < 50: return await interaction.response.send_message("Need 50 pts!", ephemeral=True)
        user["points"] -= 50
        emojis = ["🍒", "🍋", "💎"]
        res = [random.choice(emojis) for _ in range(3)]
        if res[0] == res[1] == res[2]: 
            win = 500 if res[0] == "💎" else 250
            user["points"] += win; msg = f"JACKPOT! Won {win}"
        else: msg = "Lost!"
        save_data(DATA_FILE, db)
        await interaction.response.send_message(f"{'|'.join(res)} - {msg}")

    @discord.ui.button(label="Daily Bonus", style=discord.ButtonStyle.gray, emoji="🎁")
    async def daily_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = get_data(DATA_FILE); user = init_user(db, str(interaction.user.id))
        user["points"] += 500; save_data(DATA_FILE, db)
        await interaction.response.send_message("You claimed 500 points!")

# ==========================================
# PREFIX COMMANDS
# ==========================================

@bot.command()
async def minigames(ctx):
    """Main menu with buttons"""
    embed = discord.Embed(title="🎮 Game Console", description="Select a game below! (Standard bets apply)", color=0x3498db)
    await ctx.send(embed=embed, view=MinigameMenu(ctx))

@bot.command()
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author
    db = get_data(DATA_FILE); user = init_user(db, str(member.id))
    await ctx.send(f"👤 **{member.display_name}** has **{user['points']:,}** points.")

@bot.command()
@commands.has_permissions(administrator=True)
async def admin_give(ctx, member: discord.Member, amount: int):
    db = get_data(DATA_FILE); user = init_user(db, str(member.id))
    user["points"] += amount; save_data(DATA_FILE, db)
    await ctx.send(f"✅ Gave {amount} to {member.mention}")

# Earning by chatting
@bot.event
async def on_message(message):
    if message.author.bot: return
    db = get_data(DATA_FILE); user = init_user(db, str(message.author.id))
    user["points"] += 1; save_data(DATA_FILE, db)
    await bot.process_commands(message)

bot.run(TOKEN)
