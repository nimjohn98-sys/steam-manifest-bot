import discord
from discord.ext import commands
import random
import asyncio

# ==========================================
# ⚙️ GLOBAL ENGINE CONFIG
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

DB = {}
GLOBAL_JACKPOT = 50000
KOTH_DATA = {"king_id": None, "king_name": "No One"}
WIN_TAX = 0.01 

def get_u(uid, name="User"):
    uid = str(uid)
    if uid not in DB: DB[uid] = {"points": 1000, "inv": [], "name": name}
    return DB[uid]

# ==========================================
# 🎰 UNIVERSAL BETTING MODAL
# ==========================================
class BetModal(discord.ui.Modal, title='🏦 Steam Casino: Enter Bet'):
    amount = discord.ui.TextInput(label='Bet Amount', placeholder='e.g. 500')
    def __init__(self, game_name):
        super().__init__()
        self.game = game_name

    async def on_submit(self, interaction: discord.Interaction):
        try: bet = int(self.amount.value)
        except: return await interaction.response.send_message("❌ Use numbers only.", ephemeral=True)
        
        u = get_u(interaction.user.id, interaction.user.name)
        if bet <= 0 or u["points"] < bet: return await interaction.response.send_message("❌ Not enough points!", ephemeral=True)
        
        u["points"] -= bet
        global GLOBAL_JACKPOT

        # --- REAL WORLD MATH LOGIC ---
        if "Crash" in self.game:
            view = LiveCrash(interaction.user.id, bet)
            await interaction.response.send_message(f"📈 Opening **{self.game}** Market...", view=view)
            msg = await interaction.original_response()
            return bot.loop.create_task(view.market_tick(msg))

        # Win calculation based on IRL Odds
        win = False
        multi = 2.0
        if "Slots" in self.game: win = random.random() < 0.25; multi = 5.0
        elif "Roulette" in self.game: win = random.random() < 0.47; multi = 2.0
        elif "Coinflip" in self.game: win = random.random() < 0.50; multi = 2.0
        else: win = random.random() < 0.48; multi = 2.0

        if win:
            winnings = int(bet * multi)
            tax = int(winnings * WIN_TAX)
            net = winnings - tax
            u["points"] += net
            if KOTH_DATA["king_id"]: get_u(KOTH_DATA["king_id"])["points"] += tax
            await interaction.response.send_message(f"✅ **WIN!** +{net} pts on {self.game}. (Tax: {tax})")
        else:
            GLOBAL_JACKPOT += int(bet * 0.10)
            await interaction.response.send_message(f"❌ **LOSS.** {self.game} took your {bet} pts.")

# ==========================================
# 📈 LIVE CRYPTO MARKET (CRASH)
# ==========================================
class LiveCrash(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(); self.uid, self.bet, self.m, self.active = uid, bet, 1.0, True
        self.crash_at = round(random.uniform(1.1, 4.0), 2)

    @discord.ui.button(label="SELL / CASH OUT", style=discord.ButtonStyle.green, emoji="💰")
    async def sell(self, i, b):
        if not self.active or i.user.id != self.uid: return
        self.active = False
        u = get_u(self.uid)
        u["points"] += int(self.bet * self.m)
        await i.response.edit_message(content=f"💰 **SOLD!** You exited at **{self.m}x** for **{int(self.bet * self.m)} pts**!", view=None)

    async def market_tick(self, msg):
        while self.active:
            await asyncio.sleep(1.5)
            self.m = round(self.m + 0.1, 1)
            if self.m >= self.crash_at:
                self.active = False
                await msg.edit(content=f"📉 **MARKET CRASH!** Dropped at **{self.m}x**. You lost your position.", view=None)
                break
            await msg.edit(content=f"📈 **Market Rising...** Multiplier: **{self.m}x**")

# ==========================================
# 🖥️ THE HUB (BUTTONS + DROPDOWNS)
# ==========================================
class SectorSelect(discord.ui.Select):
    def __init__(self, label, game_list):
        options = [discord.SelectOption(label=g) for g in game_list]
        super().__init__(placeholder=label, options=options)
    async def callback(self, i): await i.response.send_modal(BetModal(self.values[0]))

class UltimateHub(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Dropdowns for the 100 Games
        self.add_item(SectorSelect("🎰 More Casino Games", ["Baccarat", "Keno", "Video Poker", "Craps", "Mega Slots"]))
        self.add_item(SectorSelect("📈 More Crypto/Sports", ["ETH Moon", "UFC Fight", "Horse Racing", "Doge Flip"]))

    # POPULAR GAMES (Direct Buttons)
    @discord.ui.button(label="Slots", style=discord.ButtonStyle.danger, emoji="🎰", row=1)
    async def slots_btn(self, i, b): await i.response.send_modal(BetModal("Slots"))

    @discord.ui.button(label="Crash", style=discord.ButtonStyle.danger, emoji="📈", row=1)
    async def crash_btn(self, i, b): await i.response.send_modal(BetModal("Crash"))

    @discord.ui.button(label="Roulette", style=discord.ButtonStyle.danger, emoji="🎡", row=1)
    async def roul_btn(self, i, b): await i.response.send_modal(BetModal("Roulette"))

    # SYSTEM BUTTONS
    @discord.ui.button(label="Claim King (500)", style=discord.ButtonStyle.primary, emoji="👑", row=2)
    async def claim_btn(self, i, b):
        u = get_u(i.user.id)
        if u["points"] < 500: return await i.response.send_message("❌ Need 500 pts!", ephemeral=True)
        u["points"] -= 500
        KOTH_DATA["king_id"], KOTH_DATA["king_name"] = i.user.id, i.user.name
        await i.response.send_message(f"👑 **{i.user.name}** is the King! All winners pay you 1% tax!")

# ==========================================
# 🚀 CORE
# ==========================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_message(m):
    if not m.author.bot: get_u(m.author.id, m.author.name)["points"] += 1
    await bot.process_commands(m)

@bot.command()
async def hub(ctx):
    u = get_u(ctx.author.id, ctx.author.name)
    embed = discord.Embed(title="🌐 Steam Global Hub v18", color=0x1b2838)
    embed.add_field(name="👤 Your Balance", value=f"🪙 **{u['points']} pts**")
    embed.add_field(name="👑 Current King", value=KOTH_DATA['king_name'])
    embed.add_field(name="💰 Jackpot", value=f"{GLOBAL_JACKPOT} pts")
    embed.set_footer(text="Select a game button or dropdown below to play!")
    
    await ctx.send(embed=embed, view=UltimateHub())

bot.run(TOKEN)
