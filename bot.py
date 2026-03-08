import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta

# ==========================================
# ⚙️ GLOBAL CONFIGURATION
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# Role ID Mapping: [Role ID, Price]
ROLE_SHOP_CONFIG = {
    "Elite Merchant": [1480196811850252529, 25000],
    "Steam Executive": [1480196317455188100, 50000],
    "Global Monarch": [1480195969416036498, 100000]
}

# Boost Config: [Price, Multiplier, Duration (mins)]
BOOSTS = {
    "Bronze Multi (2x)": [5000, 2, 120],
    "Silver Multi (3x)": [15000, 3, 120],
    "Gold Multi (5x)": [50000, 5, 120]
}

DB = {}
GLOBAL_JACKPOT = 100000
KOTH_DATA = {"king_id": None, "king_name": "No One"}

def get_u(uid, name="User"):
    uid = str(uid)
    if uid not in DB: 
        DB[uid] = {"points": 1000, "name": name, "prestige": 0, "boost": 1, "boost_exp": None, "last_daily": None}
    return DB[uid]

def check_boost(u):
    if u["boost_exp"] and datetime.now() > u["boost_exp"]:
        u["boost"] = 1
        u["boost_exp"] = None
    return u["boost"]

# ==========================================
# 🎰 REALISTIC GAME MODALS
# ==========================================
class RouletteModal(discord.ui.Modal, title='🎡 Realistic Roulette'):
    bet_type = discord.ui.TextInput(label='Bet (Red, Black, Green, or Number 0-36)', placeholder='Red')
    amount = discord.ui.TextInput(label='Amount', placeholder='100')

    async def on_submit(self, i: discord.Interaction):
        try:
            amt = int(self.amount.value)
            choice = self.bet_type.value.lower()
        except: return await i.response.send_message("❌ Use numbers for the amount!", ephemeral=True)

        u = get_u(i.user.id)
        if u["points"] < amt: return await i.response.send_message("❌ Insufficient funds.", ephemeral=True)
        u["points"] -= amt

        msg = await i.response.send_message("🎡 **Spinning...**")
        msg = await i.original_response()

        # Animation
        for _ in range(3):
            await asyncio.sleep(0.8)
            await msg.edit(content=f"🎡 **Spinning...** [{random.randint(0,36)}]")

        res_num = random.randint(0, 36)
        res_color = "green" if res_num == 0 else ("red" if res_num % 2 != 0 else "black")
        
        win = False
        if choice == res_color or (choice.isdigit() and int(choice) == res_num):
            win = True
            multi = 35 if (choice == "green" or choice.isdigit()) else 2
            payout = amt * multi
            tax = int(payout * 0.01)
            u["points"] += (payout - tax)
            if KOTH_DATA["king_id"]: get_u(KOTH_DATA["king_id"])["points"] += tax
            await msg.edit(content=f"✅ **Landed on {res_num} ({res_color})!** You won **{payout-tax} pts**!")
        else:
            global GLOBAL_JACKPOT
            GLOBAL_JACKPOT += int(amt * 0.1)
            await msg.edit(content=f"❌ **Landed on {res_num} ({res_color}).** House wins.")

# ==========================================
# 📈 BTC CRASH ENGINE (REAL-TIME)
# ==========================================
class CrashView(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(); self.uid, self.bet, self.m, self.active = uid, bet, 1.0, True
        self.crash_at = round(random.uniform(1.1, 4.2), 2)

    @discord.ui.button(label="CASH OUT", style=discord.ButtonStyle.green, emoji="💰")
    async def sell(self, i, b):
        if not self.active or i.user.id != self.uid: return
        self.active = False
        u = get_u(self.uid)
        u["points"] += int(self.bet * self.m)
        await i.response.edit_message(content=f"💰 **Sold at {self.m}x!** +{int(self.bet * self.m)} pts", view=None)

    async def run(self, msg):
        while self.active:
            await asyncio.sleep(1.5)
            self.m = round(self.m + 0.2, 1)
            if self.m >= self.crash_at:
                self.active = False
                await msg.edit(content=f"💥 **CRASHED at {self.m}x!** You lost everything.", view=None)
                break
            await msg.edit(content=f"📈 **Market Price: {self.m}x**")

# ==========================================
# 🛍️ NAVIGATION & SHOPS
# ==========================================
class SubMenuView(discord.ui.View):
    def __init__(self, item_type):
        super().__init__(timeout=60)
        if item_type == "roles": self.add_item(RoleSelect())
        else: self.add_item(BoostSelect())

    @discord.ui.button(label="Back", style=discord.ButtonStyle.gray, emoji="⬅️")
    async def back(self, i, b):
        u = get_u(i.user.id)
        await i.response.edit_message(content=None, embed=gen_hub_embed(u), view=UltimateHub())

class RoleSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=n, description=f"{d[1]} pts") for n, d in ROLE_SHOP_CONFIG.items()]
        super().__init__(placeholder="Select a Role...", options=options)
    async def callback(self, i):
        u = get_u(i.user.id); name = self.values[0]; rid, price = ROLE_SHOP_CONFIG[name]
        if u["points"] < price: return await i.response.send_message("❌ No cash.", ephemeral=True)
        role = i.guild.get_role(rid)
        try: await i.user.add_roles(role); u["points"] -= price; await i.response.send_message(f"✅ {name} Equipped!", ephemeral=True)
        except: await i.response.send_message("❌ Role error.", ephemeral=True)

class BoostSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=n, description=f"{d[0]} pts") for n, d in BOOSTS.items()]
        super().__init__(placeholder="Select a Boost...", options=options)
    async def callback(self, i):
        u = get_u(i.user.id); name = self.values[0]; p, m, d = BOOSTS[name]
        if u["points"] < p: return await i.response.send_message("❌ No cash.", ephemeral=True)
        u["points"] -= p; u["boost"] = m; u["boost_exp"] = datetime.now() + timedelta(minutes=d)
        await i.response.send_message(f"🚀 {m}x Boost Active!", ephemeral=True)

# ==========================================
# 🖥️ THE OMNI HUB
# ==========================================
def gen_hub_embed(u):
    b_stat = f"{u['boost']}x" if check_boost(u) > 1 else "None"
    e = discord.Embed(title="🌐 Steam Omni-Hub v25", color=0x1b2838)
    e.add_field(name="Wallet", value=f"🪙 {u['points']} pts")
    e.add_field(name="Multiplier", value=f"🚀 {b_stat}")
    e.add_field(name="King", value=KOTH_DATA["king_name"])
    e.set_footer(text=f"Prestige: {u['prestige']} | Jackpot: {GLOBAL_JACKPOT}")
    return e

class UltimateHub(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="Daily", style=discord.ButtonStyle.success, emoji="📅", row=0)
    async def daily(self, i, b):
        u = get_u(i.user.id)
        u["points"] += (5000 * check_boost(u))
        await i.response.send_message(f"💰 Daily Claimed! (Boost applied)", ephemeral=True)

    @discord.ui.button(label="Roles", style=discord.ButtonStyle.primary, emoji="🎭", row=0)
    async def roles(self, i, b): await i.response.edit_message(content="🎭 **Role Shop**", embed=None, view=SubMenuView("roles"))

    @discord.ui.button(label="Boosts", style=discord.ButtonStyle.primary, emoji="🚀", row=0)
    async def boosts(self, i, b): await i.response.edit_message(content="🚀 **Boost Shop**", embed=None, view=SubMenuView("boosts"))

    @discord.ui.button(label="Roulette", style=discord.ButtonStyle.danger, emoji="🎡", row=1)
    async def roul(self, i, b): await i.response.send_modal(RouletteModal())

    @discord.ui.button(label="Crash", style=discord.ButtonStyle.danger, emoji="📈", row=1)
    async def crash(self, i, b):
        u = get_u(i.user.id); u["points"] -= 500
        v = CrashView(i.user.id, 500); await i.response.send_message("📉 Loading Market...", view=v)
        m = await i.original_response(); await v.run(m)

    @discord.ui.button(label="Claim King (5k)", style=discord.ButtonStyle.secondary, emoji="👑", row=2)
    async def king(self, i, b):
        u = get_u(i.user.id)
        if u["points"] < 5000: return await i.response.send_message("❌ Need 5,000 pts.", ephemeral=True)
        u["points"] -= 5000; KOTH_DATA["king_id"], KOTH_DATA["king_name"] = i.user.id, i.user.name
        await i.response.send_message(f"👑 {i.user.name} is the new King!")

# ==========================================
# 🚀 CORE EXECUTION
# ==========================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_message(m):
    if not m.author.bot:
        u = get_u(m.author.id, m.author.name)
        u["points"] += (1 * check_boost(u))
    await bot.process_commands(m)

@bot.command()
async def hub(ctx):
    await ctx.send(embed=gen_hub_embed(get_u(ctx.author.id)), view=UltimateHub())

bot.run(TOKEN)
