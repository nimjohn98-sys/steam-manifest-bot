import discord
from discord.ext import commands
import random
import asyncio
import json
import os
from datetime import datetime, timedelta

# ==============================================================================
# ⚙️ GLOBAL SYSTEM CONFIGURATION (Line 15)
# ==============================================================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# 20 GAME MECHANICS (Column A)
MECHANICS = [
    "Slots", "Roulette", "Crash", "Baccarat", "Blackjack", 
    "Keno", "Mines", "Plinko", "Dice", "Wheel", 
    "Video Poker", "Hi-Lo", "Sic Bo", "Red Dog", "Penalty",
    "Horse Race", "Stock Call", "Shell Game", "Lottery", "Coinflip"
]

# 20 REALISTIC THEMES (Column B)
THEMES = [
    "Vegas", "Tokyo Neon", "Macau", "Crypto", "Underworld", 
    "Cyberpunk", "Wild West", "Pirate", "Medieval", "Space",
    "London", "Dubai", "Retro 80s", "Zombie", "Egyptian",
    "Arctic", "Jungle", "High Roller", "Street", "Royal"
]

# ROLE PRICING & IDS
ROLES = {
    "Elite Merchant": [1480196811850252529, 25000],
    "Steam Executive": [1480196317455188100, 50000],
    "Global Monarch": [1480195969416036498, 100000]
}

# BOOST CONFIG: [Price, Multiplier, DurationMins]
BOOSTS = {
    "Bronze 2x": [5000, 2, 120],
    "Silver 3x": [15000, 3, 120],
    "Gold 5x": [50000, 5, 120]
}

DB = {}
GLOBAL_JACKPOT = 500000
KOTH = {"id": None, "name": "No One"}

# ==============================================================================
# 📊 DATABASE & UTILITIES (Line 60)
# ==============================================================================
def get_u(uid, name="User"):
    uid = str(uid)
    if uid not in DB:
        DB[uid] = {
            "pts": 10000, 
            "name": name, 
            "prestige": 0, 
            "boost": 1, 
            "boost_exp": None, 
            "last_daily": None,
            "wins": 0,
            "losses": 0
        }
    return DB[uid]

def check_boost(u):
    if u["boost_exp"] and datetime.now() > u["boost_exp"]:
        u["boost"] = 1
        u["boost_exp"] = None
    return u["boost"]

# ==============================================================================
# 🎰 UNIVERSAL GAME ENGINE (Line 90)
# ==============================================================================
class GlobalBetModal(discord.ui.Modal, title='🎰 Game Entry'):
    bet_input = discord.ui.TextInput(label='Enter Bet Amount', placeholder='e.g. 500')
    
    def __init__(self, theme, mech):
        super().__init__()
        self.theme = theme
        self.mech = mech

    async def on_submit(self, i: discord.Interaction):
        try:
            bet = int(self.bet_input.value)
        except:
            return await i.response.send_message("❌ Error: Numbers only.", ephemeral=True)
        
        u = get_u(i.user.id, i.user.name)
        if bet <= 0 or u["pts"] < bet:
            return await i.response.send_message("❌ Error: Insufficient points.", ephemeral=True)
        
        u["pts"] -= bet
        global GLOBAL_JACKPOT

        # 🎲 THE PHYSICS SIMULATOR
        # Different themes have different house edges (Real-Life accuracy)
        edge = 0.48 if self.theme in ["High Roller", "Royal", "Vegas"] else 0.44
        
        # Game-Specific Multipliers
        multi = 2.0
        if "Slots" in self.mech: edge = 0.15; multi = 10.0
        if "Lottery" in self.mech: edge = 0.05; multi = 50.0
        if "Keno" in self.mech: edge = 0.30; multi = 4.0

        win = random.random() < edge
        
        if win:
            payout = int(bet * multi * check_boost(u))
            tax = int(payout * 0.01)
            net = payout - tax
            u["pts"] += net
            u["wins"] += 1
            # King of the Hill Tax
            if KOTH["id"]: get_u(KOTH["id"])["pts"] += tax
            await i.response.send_message(f"✅ **WIN!** [{self.theme} {self.mech}]\nYou won **{net} pts**! (Tax: {tax})")
        else:
            u["losses"] += 1
            GLOBAL_JACKPOT += int(bet * 0.1)
            await i.response.send_message(f"❌ **LOSS.** The **{self.theme}** house took your **{bet} pts**.")

# ==============================================================================
# 📈 ANIMATED GAME MODULES (Line 140)
# ==============================================================================
class CrashGame(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(timeout=60)
        self.uid, self.bet, self.m, self.active = uid, bet, 1.0, True
        self.crash_pt = round(random.uniform(1.2, 5.0), 2)

    @discord.ui.button(label="CASH OUT", style=discord.ButtonStyle.green, emoji="💰")
    async def cashout(self, i, b):
        if i.user.id != self.uid or not self.active: return
        self.active = False
        u = get_u(self.uid)
        win = int(self.bet * self.m)
        u["pts"] += win
        await i.response.edit_message(content=f"💰 **SUCCESS!** Exited at **{self.m}x**. Received **{win} pts**.", view=None)

    async def main_loop(self, msg):
        while self.active:
            await asyncio.sleep(1.5)
            self.m = round(self.m + 0.2, 1)
            if self.m >= self.crash_pt:
                self.active = False
                await msg.edit(content=f"💥 **CRASHED!** The market collapsed at **{self.m}x**.", view=None)
                break
            await msg.edit(content=f"📈 **Market Rising...** Multiplier: **{self.m}x**")

# ==============================================================================
# 🛍️ SHOP & NAVIGATION (Line 175)
# ==============================================================================
class SubMenuView(discord.ui.View):
    def __init__(self, mode):
        super().__init__(timeout=60)
        if mode == "roles": self.add_item(RoleSelector())
        elif mode == "boosts": self.add_item(BoostSelector())

    @discord.ui.button(label="Return to Hub", style=discord.ButtonStyle.gray, emoji="⬅️")
    async def back(self, i, b):
        u = get_u(i.user.id)
        await i.response.edit_message(content=None, embed=main_hub_embed(u), view=MainHubView())

class RoleSelector(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=n, description=f"Cost: {d[1]} pts") for n, d in ROLES.items()]
        super().__init__(placeholder="Select a Badge...", options=options)

    async def callback(self, i: discord.Interaction):
        u = get_u(i.user.id)
        name = self.values[0]
        rid, price = ROLES[name]
        if u["pts"] < price: return await i.response.send_message("❌ Inadequate balance.", ephemeral=True)
        role = i.guild.get_role(rid)
        try:
            await i.user.add_roles(role)
            u["pts"] -= price
            await i.response.send_message(f"✅ **{name}** has been added to your profile!", ephemeral=True)
        except:
            await i.response.send_message("❌ Permission Error: Bot role must be higher.", ephemeral=True)

class BoostSelector(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=n, description=f"{d[1]}x for {d[2]}m") for n, d in BOOSTS.items()]
        super().__init__(placeholder="Select a Multiplier...", options=options)

    async def callback(self, i: discord.Interaction):
        u = get_u(i.user.id)
        name = self.values[0]
        p, m, d = BOOSTS[name]
        if u["pts"] < p: return await i.response.send_message("❌ Inadequate balance.", ephemeral=True)
        u["pts"] -= p
        u["boost"] = m
        u["boost_exp"] = datetime.now() + timedelta(minutes=d)
        await i.response.send_message(f"🚀 **BOOST ON!** {m}x multiplier active for {d} minutes.", ephemeral=True)

# ==============================================================================
# 🌐 THE MAIN HUB INTERFACE (Line 240)
# ==============================================================================
def main_hub_embed(u):
    b_stat = f"{u['boost']}x" if check_boost(u) > 1 else "None"
    e = discord.Embed(title="🌐 Steam Global Hub v31", color=0x1b2838, timestamp=datetime.now())
    e.add_field(name="💰 Wallet", value=f"**{u['pts']} pts**", inline=True)
    e.add_field(name="🚀 Active Boost", value=f"**{b_stat}**", inline=True)
    e.add_field(name="👑 King", value=f"**{KOTH['name']}**", inline=True)
    e.add_field(name="📈 Stats", value=f"Wins: {u['wins']} | Losses: {u['losses']}", inline=False)
    e.set_footer(text=f"Total Jackpot: {GLOBAL_JACKPOT} pts")
    e.set_thumbnail(url="https://i.imgur.com/8Q0Xl9n.png") # Optional UI image
    return e

class MainHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Dropdowns for the 400 Games
        self.add_item(ThemeMenu(THEMES[:10]))
        self.add_item(ThemeMenu(THEMES[10:]))

    @discord.ui.button(label="Daily", style=discord.ButtonStyle.success, emoji="📅", row=2)
    async def daily(self, i, b):
        u = get_u(i.user.id, i.user.name)
        now = datetime.now()
        if u["last_daily"] and now < u["last_daily"] + timedelta(days=1):
            rem = (u["last_daily"] + timedelta(days=1)) - now
            return await i.response.send_message(f"⏳ Reward locked for {int(rem.total_seconds()//3600)}h.", ephemeral=True)
        
        reward = int(5000 * check_boost(u))
        u["pts"] += reward
        u["last_daily"] = now
        await i.response.edit_message(embed=main_hub_embed(u), view=self)
        await i.followup.send(f"✅ **Daily Claimed!** +{reward} pts", ephemeral=True)

    @discord.ui.button(label="Role Shop", style=discord.ButtonStyle.primary, emoji="🎭", row=2)
    async def role_btn(self, i, b):
        await i.response.edit_message(content="🎭 **Badge Marketplace**", embed=None, view=SubMenuView("roles"))

    @discord.ui.button(label="Boosters", style=discord.ButtonStyle.primary, emoji="🚀", row=2)
    async def boost_btn(self, i, b):
        await i.response.edit_message(content="🚀 **Multiplier Lab**", embed=None, view=SubMenuView("boosts"))

    @discord.ui.button(label="King", style=discord.ButtonStyle.secondary, emoji="👑", row=3)
    async def claim_king(self, i, b):
        u = get_u(i.user.id)
        if u["pts"] < 10000: return await i.response.send_message("❌ Costs 10,000 pts.", ephemeral=True)
        u["pts"] -= 10000
        KOTH["id"], KOTH["name"] = i.user.id, i.user.name
        await i.response.send_message(f"👑 **{i.user.name}** is the new King! (1% Tax on all winners)")

class ThemeMenu(discord.ui.Select):
    def __init__(self, theme_list):
        opts = [discord.SelectOption(label=t) for t in theme_list]
        super().__init__(placeholder="Step 1: Choose Sector...", options=opts)

    async def callback(self, i: discord.Interaction):
        theme = self.values[0]
        view = discord.ui.View()
        view.add_item(MechMenu(theme))
        await i.response.edit_message(content=f"📍 **Location: {theme}**\nStep 2: Choose Game Mode", view=view)

class MechMenu(discord.ui.Select):
    def __init__(self, theme):
        self.theme = theme
        opts = [discord.SelectOption(label=m) for m in MECHANICS]
        super().__init__(placeholder="Step 2: Choose Game...", options=opts)

    async def callback(self, i: discord.Interaction):
        mech = self.values[0]
        # Direct launch for Crash (special animation)
        if mech == "Crash":
            modal = CrashEntryModal(self.theme)
            await i.response.send_modal(modal)
        else:
            modal = GlobalBetModal(self.theme, mech)
            await i.response.send_modal(modal)

class CrashEntryModal(discord.ui.Modal, title="📉 Crash Investment"):
    amt = discord.ui.TextInput(label="Bet Amount")
    def __init__(self, theme): super().__init__(); self.theme = theme
    async def on_submit(self, i):
        val = int(self.amt.value)
        u = get_u(i.user.id); u["pts"] -= val
        view = CrashGame(i.user.id, val)
        await i.response.send_message(f"📉 **{self.theme} Market Opening...**", view=view)
        msg = await i.original_response(); await view.main_loop(msg)

# ==============================================================================
# 🚀 CORE EXECUTION ENGINE (Line 350)
# ==============================================================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Steam Ultimate Engine v31 Active: {bot.user}")

@bot.event
async def on_message(msg):
    if msg.author.bot: return
    
    # Message Income Logic
    u = get_u(msg.author.id, msg.author.name)
    multiplier = check_boost(u)
    u["pts"] += (1 * multiplier) # Passive income
    
    await bot.process_commands(msg)

@bot.command(name="hub")
async def hub_command(ctx):
    """Opens the Global Hub Interface"""
    u = get_u(ctx.author.id, ctx.author.name)
    await ctx.send(embed=main_hub_embed(u), view=MainHubView())

@bot.command(name="balance")
async def bal_command(ctx):
    u = get_u(ctx.author.id)
    await ctx.send(f"🪙 **{ctx.author.name}**, your balance is **{u['pts']} pts**.")

@bot.command(name="give")
@commands.has_permissions(administrator=True)
async def give_points(ctx, member: discord.Member, amount: int):
    u = get_u(member.id)
    u["pts"] += amount
    await ctx.send(f"✅ Admin added {amount} pts to {member.mention}.")

# ERROR HANDLER (Line 400)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"🛑 SYSTEM ERROR: {error}")

# ==============================================================================
# 🏁 EOF - END OF FILE (Line 410)
# ==============================================================================
bot.run(TOKEN)
