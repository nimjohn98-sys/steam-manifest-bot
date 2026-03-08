import discord
from discord.ext import commands
import random
import asyncio

# ==========================================
# ⚙️ GLOBAL REALITY ENGINE
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

DB = {}
GLOBAL_JACKPOT = 50000
KOTH_DATA = {"king_id": None, "king_name": "No One"}
WIN_TAX = 0.01 # 1% King Tax

def get_u(uid, name="Trader"):
    uid = str(uid)
    if uid not in DB: DB[uid] = {"points": 1000, "inv": [], "name": name}
    return DB[uid]

# ==========================================
# 🎰 THE UNIVERSAL ODDS CALCULATOR (100 GAMES)
# ==========================================
class BetModal(discord.ui.Modal, title='🏦 Steam Global Exchange'):
    amount = discord.ui.TextInput(label='Enter Bet Amount', placeholder='100')
    def __init__(self, game_name):
        super().__init__()
        self.game = game_name

    async def on_submit(self, interaction: discord.Interaction):
        try: bet = int(self.amount.value)
        except: return await interaction.response.send_message("❌ Numbers only.", ephemeral=True)
        
        u = get_u(interaction.user.id, interaction.user.name)
        if bet <= 0 or u["points"] < bet: return await interaction.response.send_message("❌ Insufficient funds.", ephemeral=True)
        
        u["points"] -= bet
        global GLOBAL_JACKPOT

        # --- REAL WORLD MATH ENGINE ---
        # We simulate 100 games by mapping the 'game_name' to a Risk Profile
        
        win = False
        payout_multi = 2.0
        
        # 1. High-Odds / Low Win Rate (Lottery/Slots)
        if any(x in self.game for x in ["Slots", "Lottery", "Keno", "Jackpot"]):
            win = random.random() < 0.15 # 15% Win Rate
            payout_multi = 6.0
            
        # 2. Near 50/50 (Roulette/Coinflip/Baccarat)
        elif any(x in self.game for x in ["Roulette", "Flip", "Baccarat", "Dice"]):
            win = random.random() < 0.47 # 47% (The 3% House Edge)
            payout_multi = 2.0

        # 3. High Risk / High Reward (Crypto/Crash)
        elif "Crash" in self.game or "Moon" in self.game:
            # Trigger the Live Crash View instead of instant math
            view = LiveCrash(interaction.user.id, bet)
            await interaction.response.send_message(f"📈 Opening **{self.game}** Market...", view=view)
            msg = await interaction.original_response()
            return bot.loop.create_task(view.market_tick(msg))

        # 4. Standard Skill/Luck Mix (Blackjack/War)
        else:
            win = random.random() < 0.49
            payout_multi = 2.0

        # --- SETTLEMENT ---
        if win:
            winnings = int(bet * payout_multi)
            tax = int(winnings * WIN_TAX)
            net = winnings - tax
            u["points"] += net
            if KOTH_DATA["king_id"]: get_u(KOTH_DATA["king_id"])["points"] += tax
            await interaction.response.send_message(f"✅ **WIN!** You won **{net} pts** on {self.game}! (King Tax: {tax})")
        else:
            GLOBAL_JACKPOT += int(bet * 0.10) # 10% of losses go to jackpot
            await interaction.response.send_message(f"❌ **LOSS.** The House took your {bet} pts on {self.game}.")

# ==========================================
# 📈 LIVE CRASH (REAL-TIME BTC LOGIC)
# ==========================================
class LiveCrash(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(); self.uid, self.bet, self.m, self.active = uid, bet, 1.0, True
        self.crash_at = round(random.uniform(1.1, 3.5), 2)

    @discord.ui.button(label="SELL / CASH OUT", style=discord.ButtonStyle.green, emoji="💰")
    async def sell(self, i, b):
        if not self.active or i.user.id != self.uid: return
        self.active = False
        u = get_u(self.uid)
        u["points"] += int(self.bet * self.m)
        await i.response.edit_message(content=f"💰 **SOLD!** You cashed out at **{self.m}x** for **{int(self.bet * self.m)} pts**!", view=None)

    async def market_tick(self, msg):
        while self.active:
            await asyncio.sleep(1.5)
            self.m = round(self.m + 0.1, 1)
            if self.m >= self.crash_at:
                self.active = False
                await msg.edit(content=f"📉 **CRASHED!** The market hit 0 at **{self.m}x**. You lost your position.", view=None)
                break
            await msg.edit(content=f"📈 **Market Price Rising...** Current Multiplier: **{self.m}x**")

# ==========================================
# 🖥️ HUB INTERFACE (5 SECTORS)
# ==========================================
class SectorSelect(discord.ui.Select):
    def __init__(self, label, game_list):
        options = [discord.SelectOption(label=g) for g in game_list]
        super().__init__(placeholder=label, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BetModal(self.values[0]))

class UltimateHub(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # We can define 20 games per selector easily
        self.add_item(SectorSelect("🎰 Casino Floor", ["Vegas Slots", "Mega Moolah", "Blackjack", "American Roulette", "Baccarat"]))
        self.add_item(SectorSelect("📈 Crypto Exchange", ["BTC Crash", "ETH Moon", "Doge Flip", "NFT Gamble", "Solana Long"]))
        self.add_item(SectorSelect("🐎 Sportsbook", ["Horse Racing", "Greyhounds", "UFC Fight", "NBA Draft", "Soccer Penalty"]))

    @discord.ui.button(label="Claim King (500 pts)", style=discord.ButtonStyle.danger, emoji="👑", row=3)
    async def claim(self, i, b):
        u = get_u(i.user.id)
        if u["points"] < 500: return await i.response.send_message("❌ Need 500 pts.", ephemeral=True)
        u["points"] -= 500
        KOTH_DATA["king_id"], KOTH_DATA["king_name"] = i.user.id, i.user.name
        await i.response.send_message(f"👑 **{i.user.name}** is the King! All winners now pay you 1% tax!")

# ==========================================
# 🚀 CORE
# ==========================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_message(m):
    if not m.author.bot: 
        u = get_u(m.author.id, m.author.name)
        u["points"] += 1 # Passive income
    await bot.process_commands(m)

@bot.command()
async def hub(ctx):
    await ctx.send(f"🌐 **Steam Ultimate v17**\n**King:** {KOTH_DATA['king_name']} | **Jackpot:** {GLOBAL_JACKPOT}", view=UltimateHub())

bot.run(TOKEN)
