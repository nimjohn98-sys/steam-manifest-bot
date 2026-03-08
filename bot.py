import discord
from discord.ext import commands
import random
import asyncio
import io
from datetime import datetime

# ==========================================
# ⚙️ GLOBAL CONFIGURATION
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

# "Item Name": [Price, Required Prestige]
SHOP_CONFIG = {
    "VIP License": [5000, 0],
    "Golden Profile": [10000, 0],
    "Hacker Badge": [3000, 0],
    "Diamond Rank": [25000, 1],
    "Server Legend": [50000, 2]
}

MANIFEST_COST = 40
PRESTIGE_COST = 50000

# Memory Storage
DB = {}

def get_user(uid, name="Unknown"):
    uid = str(uid)
    if uid not in DB:
        DB[uid] = {"points": 1000, "inv": ["Standard License"], "name": name, "prestige": 0}
    else:
        DB[uid]["name"] = name
    return DB[uid]

# ==========================================
# 🎁 GIFTING MODAL
# ==========================================
class GiftModal(discord.ui.Modal, title='🎁 Gift Points'):
    target_id = discord.ui.TextInput(label='Recipient User ID', placeholder='e.g. 123456789', min_length=15)
    amount = discord.ui.TextInput(label='Amount to Gift', placeholder='500')

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amt = int(self.amount.value)
            target = str(self.target_id.value)
        except:
            return await interaction.response.send_message("❌ Invalid input. Use numbers.", ephemeral=True)

        sender = get_user(interaction.user.id)
        
        if target == str(interaction.user.id):
            return await interaction.response.send_message("❌ You can't gift yourself!", ephemeral=True)
        
        if amt <= 0 or sender["points"] < amt:
            return await interaction.response.send_message(f"❌ Inadequate funds! You have {sender['points']} pts.", ephemeral=True)

        if target not in DB:
            return await interaction.response.send_message("❌ User not found in database. They must type `!hub` first!", ephemeral=True)

        # Transfer
        sender["points"] -= amt
        DB[target]["points"] += amt
        
        await interaction.response.send_message(f"✅ Gifted **{amt}** points to **{DB[target]['name']}**!")

# ==========================================
# 🛒 SHOP & GAMES
# ==========================================
class ShopSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=n, description=f"{p[0]} pts (Req: P{p[1]})") 
            for n, p in SHOP_CONFIG.items()
        ]
        super().__init__(placeholder="Browse the Market...", options=options)

    async def callback(self, interaction: discord.Interaction):
        item = self.values[0]
        price, req_p = SHOP_CONFIG[item]
        u = get_user(interaction.user.id)
        
        if u["prestige"] < req_p:
            return await interaction.response.send_message(f"❌ This item requires Prestige **{req_p}**!", ephemeral=True)
        if u["points"] < price:
            return await interaction.response.send_message("❌ Low funds!", ephemeral=True)
        
        u["points"] -= price
        u["inv"].append(item)
        await interaction.response.send_message(f"✅ Purchased {item}!", ephemeral=True)

# ==========================================
# 🖥️ HUB VIEW
# ==========================================
class UltimateHub(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="Profile", style=discord.ButtonStyle.secondary, emoji="👤", row=0)
    async def profile(self, interaction, b):
        u = get_user(interaction.user.id, interaction.user.name)
        e = discord.Embed(title=f"👤 {interaction.user.name}", color=0x3498db)
        e.add_field(name="Wallet", value=f"🪙 {u['points']} pts")
        e.add_field(name="Prestige", value=f"⭐ Level {u['prestige']}")
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="Gift Points", style=discord.ButtonStyle.primary, emoji="🎁", row=0)
    async def gift(self, interaction, b):
        await interaction.response.send_modal(GiftModal())

    @discord.ui.button(label="Prestige", style=discord.ButtonStyle.primary, emoji="⭐", row=0)
    async def prestige(self, interaction, b):
        u = get_user(interaction.user.id)
        if u["points"] < PRESTIGE_COST:
            return await interaction.response.send_message(f"❌ Prestige requires {PRESTIGE_COST} points!", ephemeral=True)
        u["points"] = 1000
        u["prestige"] += 1
        await interaction.response.send_message(f"✨ **{interaction.user.name}** reached Prestige **{u['prestige']}**!", ephemeral=False)

    @discord.ui.button(label="Shop", style=discord.ButtonStyle.success, emoji="🛒", row=1)
    async def shop(self, interaction, b):
        v = discord.ui.View(); v.add_item(ShopSelect())
        await interaction.response.send_message("🛍️ **Steam Market**", view=v, ephemeral=True)

    @discord.ui.button(label="Leaderboard", style=discord.ButtonStyle.secondary, emoji="🏆", row=1)
    async def lb(self, interaction, b):
        sorted_users = sorted(DB.items(), key=lambda x: (x[1]['prestige'], x[1]['points']), reverse=True)
        e = discord.Embed(title="🏆 Leaderboard", color=0xf1c40f)
        desc = ""
        for i, (uid, data) in enumerate(sorted_users[:10], 1):
            desc += f"#{i} [P{data['prestige']}] {data['name']} — `{data['points']} pts`\n"
        e.description = desc or "Empty."
        await interaction.response.send_message(embed=e, ephemeral=True)

# ==========================================
# 🚀 BOT CORE
# ==========================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_message(message):
    if message.author.bot: return
    u = get_user(message.author.id, message.author.name)
    u["points"] += (1 + u["prestige"])
    await bot.process_commands(message)

@bot.command()
async def hub(ctx):
    await ctx.send(embed=discord.Embed(title="🌐 Steam Global Hub v9", color=0x1b2838), view=UltimateHub())

@bot.event
async def on_ready(): print(f"✅ V9 Online: {bot.user}")

bot.run(TOKEN)
