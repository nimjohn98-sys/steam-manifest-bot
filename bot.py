import discord
from discord.ext import commands
import random
import asyncio
import io
from datetime import datetime

# ==========================================
# ⚙️ CONFIG & TOKEN
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
MANIFEST_COST = 40

# Memory-based Storage (Resets on restart)
DB = {}

def get_user(uid):
    uid = str(uid)
    if uid not in DB:
        DB[uid] = {"points": 1000, "inv": ["Steam License v1.0"], "xp": 0}
    return DB[uid]

# ==========================================
# 💰 THE MODAL (BETTING WINDOW)
# ==========================================
class BetWindow(discord.ui.Modal, title='Steam Wallet: Place Bet'):
    amount = discord.ui.TextInput(label='Enter Bet Amount', placeholder='e.g. 50', min_length=1, max_length=6)

    def __init__(self, game_key):
        super().__init__()
        self.game_key = game_key

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet = int(self.amount.value)
        except:
            return await interaction.response.send_message("❌ Invalid number!", ephemeral=True)

        user = get_user(interaction.user.id)
        if bet <= 0 or user["points"] < bet:
            return await interaction.response.send_message(f"❌ Low balance! You have {user['points']} pts.", ephemeral=True)

        # Deduct bet and launch game
        user["points"] -= bet
        
        if self.game_key == "blackjack":
            view = BlackjackGame(interaction.user.id, bet)
            await interaction.response.send_message(embed=view.get_embed(), view=view)
        
        elif self.game_key == "slots":
            icons = ["💎", "🍒", "🍋", "🔔", "⭐"]
            res = [random.choice(icons) for _ in range(3)]
            win = bet * 10 if res[0]==res[1]==res[2] else (bet * 2 if res[0]==res[1] else 0)
            user["points"] += win
            await interaction.response.send_message(f"🎰 | {' | '.join(res)} | 🎰\n" + (f"✅ **WIN! +{win}**" if win > 0 else "❌ **LOST**"))

        elif self.game_key == "coinflip":
            win = random.choice([True, False])
            res = "HEADS" if win else "TAILS"
            if win: user["points"] += bet * 2
            await interaction.response.send_message(f"🪙 **{res}**! " + (f"Won {bet*2}!" if win else "Lost bet."))

        elif self.game_key == "crash":
            view = CrashGame(interaction.user.id, bet)
            await interaction.response.send_message(embed=discord.Embed(title="📈 CRASH", color=0xf1c40f), view=view)
            msg = await interaction.original_response()
            bot.loop.create_task(view.run(msg))

# ==========================================
# 🎮 GAME ENGINES (Logic Classes)
# ==========================================

# --- Blackjack ---
class BlackjackGame(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(timeout=60)
        self.uid, self.bet = str(uid), bet
        cards = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        self.p_hand = [random.choice(cards), random.choice(cards)]
        self.d_hand = [random.choice(cards), random.choice(cards)]

    def score(self, hand):
        val = 0
        aces = 0
        for c in hand:
            if c in ['J','Q','K']: val += 10
            elif c == 'A': val += 11; aces += 1
            else: val += int(c)
        while val > 21 and aces: val -= 10; aces -= 1
        return val

    def get_embed(self, final=False):
        e = discord.Embed(title="🃏 Blackjack Table", color=0x2ecc71)
        e.add_field(name="Your Hand", value=f"{' '.join(self.p_hand)}\n(`{self.score(self.p_hand)}`)")
        d_val = self.score(self.d_hand) if final else "?"
        d_cards = ' '.join(self.d_hand) if final else f"{self.d_hand[0]} ❓"
        e.add_field(name="Dealer", value=f"{d_cards}\n(`{d_val}`)")
        return e

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple)
    async def hit(self, interaction: discord.Interaction, b: discord.ui.Button):
        self.p_hand.append(random.choice(['2','3','4','5','6','7','8','9','10','J','Q','K','A']))
        if self.score(self.p_hand) > 21:
            await interaction.response.edit_message(content="💥 BUST!", embed=self.get_embed(True), view=None)
        else:
            await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, b: discord.ui.Button):
        while self.score(self.d_hand) < 17: self.d_hand.append(random.choice(['2','3','4','5','6','7','8','9','10','J','Q','K','A']))
        ps, ds = self.score(self.p_hand), self.score(self.d_hand)
        res = "✅ WON!" if ds > 21 or ps > ds else ("❌ LOST." if ps < ds else "🤝 PUSH.")
        user = get_user(self.uid)
        if "WON" in res: user["points"] += self.bet * 2
        elif "PUSH" in res: user["points"] += self.bet
        await interaction.response.edit_message(content=res, embed=self.get_embed(True), view=None)

# --- Crash ---
class CrashGame(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(timeout=None)
        self.uid, self.bet, self.m, self.end = str(uid), bet, 1.0, False
        self.boom = round(random.uniform(1.2, 4.0), 2)

    @discord.ui.button(label="CASH OUT", style=discord.ButtonStyle.green)
    async def stop(self, interaction: discord.Interaction, b: discord.ui.Button):
        if self.end: return
        self.end = True
        get_user(self.uid)["points"] += int(self.bet * self.m)
        await interaction.response.edit_message(content=f"💰 Cashed at **{self.m}x**!", view=None)

    async def run(self, msg):
        while not self.end:
            await asyncio.sleep(1)
            self.m = round(self.m + 0.2, 1)
            if self.m >= self.boom:
                self.end = True
                await msg.edit(content=f"💥 CRASHED at **{self.m}x**!", embed=None, view=None)
                break
            await msg.edit(embed=discord.Embed(title=f"📈 Multiplier: {self.m}x", color=0xf1c40f))

# ==========================================
# 🖥️ THE EASY-TO-ADD GUI (The Hub)
# ==========================================
class UltimateHub(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # --- ROW 0: SYSTEM UTILS ---
    @discord.ui.button(label="Manifest (40 pts)", style=discord.ButtonStyle.primary, emoji="💾", row=0)
    async def manifest(self, interaction: discord.Interaction, b: discord.ui.Button):
        user = get_user(interaction.user.id)
        if user["points"] < MANIFEST_COST:
            return await interaction.response.send_message("❌ Inadequate funds for Manifest.", ephemeral=True)
        
        user["points"] -= MANIFEST_COST
        
        # CREATE DOWNLOADABLE FILE
        log = f"--- STEAM SYSTEM REPORT ---\nUSER: {interaction.user}\nID: {interaction.user.id}\nWALLET: {user['points']} pts\nTIMESTAMP: {datetime.now()}"
        file = discord.File(fp=io.BytesIO(log.encode()), filename="steam_manifest.txt")
        await interaction.response.send_message("✅ Manifest processed. Data packet attached:", file=file)

    @discord.ui.button(label="Daily +500", style=discord.ButtonStyle.success, emoji="🎁", row=0)
    async def daily(self, interaction: discord.Interaction, b: discord.ui.Button):
        get_user(interaction.user.id)["points"] += 500
        await interaction.response.send_message("🎁 500 points added to your Steam Wallet!", ephemeral=True)

    # --- ROW 1: GAMING SUITE ---
    @discord.ui.button(label="Blackjack", style=discord.ButtonStyle.danger, emoji="🃏", row=1)
    async def play_bj(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(BetWindow("blackjack"))

    @discord.ui.button(label="Slots", style=discord.ButtonStyle.danger, emoji="🎰", row=1)
    async def play_sl(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(BetWindow("slots"))

    @discord.ui.button(label="Crash", style=discord.ButtonStyle.danger, emoji="📈", row=1)
    async def play_cr(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(BetWindow("crash"))

    @discord.ui.button(label="Coinflip", style=discord.ButtonStyle.danger, emoji="🪙", row=1)
    async def play_cf(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(BetWindow("coinflip"))

# ==========================================
# 🚀 BOT INITIALIZATION
# ==========================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.command()
async def hub(ctx):
    """The main entry point for the Easy-GUI"""
    embed = discord.Embed(
        title="🌐 Steam Global Interface",
        description="Select a system utility (Row 0) or launch a gaming protocol (Row 1).",
        color=0x1b2838
    )
    await ctx.send(embed=embed, view=UltimateHub())

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")

bot.run(TOKEN)
