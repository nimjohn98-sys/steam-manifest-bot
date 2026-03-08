import discord
from discord.ext import commands
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

# ==========================================
# ⚙️ CONFIGURATION & TOKEN
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
DATA_FILE = "manifest_database.json"
MANIFEST_FEE = 40

class UltimateEngine(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def on_ready(self):
        print(f'🚀 STEAM ENGINE + MANIFEST ONLINE: {self.user}')
        print(f'📡 Ready for !hub or !manifest (Cost: {MANIFEST_FEE})')

bot = UltimateEngine()

# ==========================================
# 💾 DATABASE SYSTEM
# ==========================================
def load_db():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(uid):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {
            "points": 1000, 
            "inventory": ["Standard User License"], 
            "stats": {"games_played": 0, "total_won": 0},
            "last_daily": None
        }
        save_db(db)
    return db[uid]

def update_user(uid, data):
    db = load_db()
    db[str(uid)] = data
    save_db(db)

# ==========================================
# 💸 BETTING MODAL (The Pay-to-Play System)
# ==========================================
class BetModal(discord.ui.Modal, title='Place Your Bet'):
    bet_input = discord.ui.TextInput(label='Enter Bet Amount', placeholder='e.g. 250', required=True)

    def __init__(self, game):
        super().__init__()
        self.game = game

    async def on_submit(self, interaction: discord.Interaction):
        try: 
            bet = int(self.bet_input.value)
        except: 
            return await interaction.response.send_message("❌ Please enter a whole number.", ephemeral=True)

        u = get_user(interaction.user.id)
        if bet <= 0 or u["points"] < bet:
            return await interaction.response.send_message(f"❌ You only have **{u['points']}** points.", ephemeral=True)

        u["points"] -= bet
        u["stats"]["games_played"] += 1
        update_user(interaction.user.id, u)

        if self.game == "blackjack":
            v = BlackjackView(interaction.user.id, bet)
            await interaction.response.send_message(embed=v.get_embed(), view=v)
        
        elif self.game == "slots":
            icons = ["🍒", "💎", "🍋", "🔔", "⭐"]
            res = [random.choice(icons) for _ in range(3)]
            win = bet * 15 if res[0]==res[1]==res[2] == "💎" else (bet * 5 if res[0]==res[1]==res[2] else 0)
            u = get_user(interaction.user.id); u["points"] += win; update_user(interaction.user.id, u)
            await interaction.response.send_message(f"🎰 | {' | '.join(res)} | 🎰\n" + (f"✨ **WINNER! +{win} pts**" if win > 0 else "💀 Lost bet."))

# ==========================================
# 🃏 MINIGAMES (Blackjack & Logic)
# ==========================================
class BlackjackView(discord.ui.View):
    def __init__(self, user_id, bet):
        super().__init__(timeout=60)
        self.uid, self.bet = str(user_id), bet
        self.deck = [v for v in ['2','3','4','5','6','7','8','9','10','J','Q','K','A'] for _ in range(4)]
        random.shuffle(self.deck)
        self.p_hand, self.d_hand = [self.deck.pop(), self.deck.pop()], [self.deck.pop(), self.deck.pop()]

    def calc(self, hand):
        v, a = 0, 0
        for c in hand:
            if c in ['J','Q','K']: v += 10
            elif c == 'A': v += 11; a += 1
            else: v += int(c)
        while v > 21 and a: v -= 10; a -= 1
        return v

    def get_embed(self, done=False):
        pv, dv = self.calc(self.p_hand), self.calc(self.d_hand)
        e = discord.Embed(title="🃏 Blackjack", color=0x2ecc71)
        e.add_field(name=f"You ({pv})", value=" ".join(self.p_hand))
        if done: e.add_field(name=f"Dealer ({dv})", value=" ".join(self.d_hand))
        else: e.add_field(name="Dealer (?)", value=f"{self.d_hand[0]} ❓")
        return e

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple)
    async def hit(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        self.p_hand.append(self.deck.pop())
        if self.calc(self.p_hand) > 21: await self.end(interaction, "BUST!", False)
        else: await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        while self.calc(self.d_hand) < 17: self.d_hand.append(self.deck.pop())
        pv, dv = self.calc(self.p_hand), self.calc(self.d_hand)
        res = "WIN!" if dv > 21 or pv > dv else ("LOSE." if pv < dv else "PUSH.")
        await self.end(interaction, res, "WIN" in res or "PUSH" in res)

    async def end(self, interaction, res, payout):
        u = get_user(self.uid)
        if "WIN" in res: u["points"] += self.bet * 2
        elif "PUSH" in res: u["points"] += self.bet
        update_user(self.uid, u)
        await interaction.response.edit_message(content=f"**{res}**", embed=self.get_embed(True), view=None)

# ==========================================
# 🖥️ HUB & MANIFEST INTERFACE
# ==========================================
class HubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Steam Manifest (40 pts)", style=discord.ButtonStyle.primary, emoji="📄", row=0)
    async def manifest_btn(self, interaction: discord.Interaction, btn: discord.ui.Button):
        u = get_user(interaction.user.id)
        if u["points"] < MANIFEST_FEE:
            return await interaction.response.send_message(f"❌ Manifest access costs **{MANIFEST_FEE} pts**.", ephemeral=True)
        
        u["points"] -= MANIFEST_FEE
        update_user(interaction.user.id, u)

        e = discord.Embed(title="📟 Steam Digital Manifest", color=0x1b2838)
        e.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        e.add_field(name="Points", value=f"🪙 {u['points']}")
        e.add_field(name="Software Library", value="\n".join([f"• {i}" for i in u['inventory']]))
        e.add_field(name="Usage Stats", value=f"Games Played: {u['stats']['games_played']}")
        await interaction.response.send_message(embed=e)

    @discord.ui.button(label="Daily Points", style=discord.ButtonStyle.success, emoji="🎁", row=0)
    async def daily(self, interaction: discord.Interaction, btn: discord.ui.Button):
        u = get_user(interaction.user.id); u["points"] += 500; update_user(interaction.user.id, u)
        await interaction.response.send_message("✅ +500 daily points added!", ephemeral=True)

    @discord.ui.button(label="Play Blackjack", style=discord.ButtonStyle.danger, emoji="🃏", row=1)
    async def bj(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await interaction.response.send_modal(BetModal("blackjack"))

    @discord.ui.button(label="Play Slots", style=discord.ButtonStyle.danger, emoji="🎰", row=1)
    async def slots(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await interaction.response.send_modal(BetModal("slots"))

@bot.command()
async def hub(ctx):
    """Entry point for the Dashboard"""
    e = discord.Embed(title="🌐 The Ultimate Hub", description=f"Manifest generation: **{MANIFEST_FEE} pts**\nUse the buttons below to interact.", color=0x2c3e50)
    await ctx.send(embed=e, view=HubView())

@bot.command()
async def manifest(ctx):
    """Direct manifest command with 40pt fee"""
    u = get_user(ctx.author.id)
    if u["points"] < MANIFEST_FEE:
        return await ctx.send(f"❌ You need {MANIFEST_FEE} points.")
    
    u["points"] -= MANIFEST_FEE
    update_user(ctx.author.id, u)
    e = discord.Embed(title="📟 Paid Steam Manifest", description=f"Points: **{u['points']}**\nSoftware: **{', '.join(u['inventory'])}**", color=0x1b2838)
    await ctx.send(embed=e)

bot.run(TOKEN)
