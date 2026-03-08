import discord
from discord.ext import commands
import random
import asyncio

# ==========================================
# ⚙️ GLOBAL CONFIG
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

DB = {}
GLOBAL_JACKPOT = 75000
PRESTIGE_COST = 50000
SHOP_ITEMS = {"Diamond Badge": 10000, "Golden Profile": 25000, "Server Ghost": 100000}

def get_u(uid, name="User"):
    uid = str(uid)
    if uid not in DB: DB[uid] = {"points": 1000, "inv": [], "name": name, "prestige": 0}
    return DB[uid]

# ==========================================
# 🛒 SHOP & MODALS
# ==========================================
class ShopSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=n, description=f"Cost: {p} pts") for n, p in SHOP_ITEMS.items()]
        super().__init__(placeholder="Select an item from the Steam Market...", options=options)

    async def callback(self, i: discord.Interaction):
        u = get_u(i.user.id)
        item = self.values[0]
        price = SHOP_ITEMS[item]
        if u["points"] < price: return await i.response.send_message("❌ Inadequate funds!", ephemeral=True)
        u["points"] -= price
        u["inv"].append(item)
        await i.response.send_message(f"✅ Purchased **{item}**!", ephemeral=True)

class BetModal(discord.ui.Modal, title='🎰 Place Your Bet'):
    amount = discord.ui.TextInput(label='Bet Amount', placeholder='100')
    def __init__(self, game): super().__init__(); self.game = game

    async def on_submit(self, i: discord.Interaction):
        try: bet = int(self.amount.value)
        except: return await i.response.send_message("❌ Numbers only.", ephemeral=True)
        u = get_u(i.user.id)
        if bet <= 0 or u["points"] < bet: return await i.response.send_message("❌ Insufficient points.", ephemeral=True)
        
        u["points"] -= bet
        # Simple IRL Math (95% RTP for Slots, 48% for others)
        win = random.random() < (0.48 if "Slots" not in self.game else 0.35)
        if win:
            multi = 10.0 if "Slots" in self.game else 2.0
            u["points"] += int(bet * multi)
            await i.response.send_message(f"✅ **WIN!** You won **{int(bet*multi)} pts** on {self.game}!")
        else:
            await i.response.send_message(f"❌ **LOSS.** {self.game} took your bet.")

# ==========================================
# 🖥️ THE RE-CONSTRUCTED HUB
# ==========================================
class SectorSelect(discord.ui.Select):
    def __init__(self, label, games):
        super().__init__(placeholder=label, options=[discord.SelectOption(label=g) for g in games])
    async def callback(self, i): await i.response.send_modal(BetModal(self.values[0]))

class UltimateHub(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Row 2 & 3: The 100 Games
        self.add_item(SectorSelect("🎰 More Casino Games", ["Baccarat", "Keno", "Video Poker", "Craps", "Bingo"]))
        self.add_item(SectorSelect("📈 Crypto & Sports", ["BTC Long", "ETH Short", "Horse Racing", "UFC Duel"]))

    # ROW 0: MANAGEMENT
    @discord.ui.button(label="Shop", style=discord.ButtonStyle.success, emoji="🛒", row=0)
    async def shop(self, i, b):
        v = discord.ui.View(); v.add_item(ShopSelect())
        await i.response.send_message("🛍️ **Steam Market**", view=v, ephemeral=True)

    @discord.ui.button(label="Prestige", style=discord.ButtonStyle.primary, emoji="⭐", row=0)
    async def prestige(self, i, b):
        u = get_u(i.user.id)
        if u["points"] < PRESTIGE_COST: return await i.response.send_message(f"❌ Prestige requires {PRESTIGE_COST} pts!", ephemeral=True)
        u["points"] = 1000
        u["prestige"] += 1
        await i.response.send_message(f"✨ **PRESTIGE UP!** {i.user.name} is now Prestige **{u['prestige']}**!")

    @discord.ui.button(label="Leaderboard", style=discord.ButtonStyle.secondary, emoji="🏆", row=0)
    async def lb(self, i, b):
        top = sorted(DB.items(), key=lambda x: x[1]['points'], reverse=True)[:5]
        board = "\n".join([f"#{idx+1} {v['name']}: {v['points']} pts" for idx, (k, v) in enumerate(top)])
        await i.response.send_message(f"🏆 **Richest Players**\n{board or 'No data.'}", ephemeral=True)

    # ROW 1: INSTANT GAMES
    @discord.ui.button(label="Slots", style=discord.ButtonStyle.danger, emoji="🎰", row=1)
    async def slots(self, i, b): await i.response.send_modal(BetModal("Slots"))

    @discord.ui.button(label="Crash", style=discord.ButtonStyle.danger, emoji="📈", row=1)
    async def crash(self, i, b): await i.response.send_modal(BetModal("Crash"))

# ==========================================
# 🚀 CORE
# ==========================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_message(m):
    if not m.author.bot:
        u = get_u(m.author.id, m.author.name)
        u["points"] += (1 + (u["prestige"] * 5)) # prestige adds 5pts per msg
    await bot.process_commands(m)

@bot.command()
async def hub(ctx):
    u = get_u(ctx.author.id, ctx.author.name)
    e = discord.Embed(title="🌐 Steam Global Hub v19", color=0x1b2838)
    e.add_field(name="Balance", value=f"🪙 {u['points']} pts")
    e.add_field(name="Rank", value=f"⭐ Prestige {u['prestige']}")
    await ctx.send(embed=e, view=UltimateHub())

bot.run(TOKEN)
