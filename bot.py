import discord
from discord.ext import commands, tasks
import random
import asyncio
import datetime
import json
import os

# --- 1. CORE CONFIGURATION ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Persistence System
DB_FILE = "titan_data.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

economy = load_data()

def get_profile(uid):
    uid = str(uid)
    if uid not in economy:
        economy[uid] = {
            "points": 1000, 
            "multi": 1.0, 
            "rebirths": 0, 
            "shields": 0,
            "job": "Unemployed", 
            "last_daily": None, 
            "last_work": None,
            "inventory": [], 
            "xp": 0,
            "level": 1,
            "fish_caught": 0,
            "animals_hunted": 0
        }
    return economy[uid]

# --- 2. THE ITEM DATABASE ---
ITEMS = {
    "Bronze_Rod": {"cost": 500, "type": "tool", "desc": "Better fishing chances."},
    "Iron_Pickaxe": {"cost": 1500, "type": "tool", "desc": "Mine 2x more ore."},
    "Hunting_Rifle": {"cost": 5000, "type": "tool", "desc": "Unlock the !hunt command."},
    "Shield_Battery": {"cost": 250, "type": "consumable", "desc": "+1 Shield."},
    "XP_Boost": {"cost": 1000, "type": "consumable", "desc": "Level up faster."}
}

# --- 3. UI COMPONENTS (THE HUB) ---

class EmpireHubView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="⚒️ Mine", style=discord.ButtonStyle.blurple, row=0)
    async def mine(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        data = get_profile(self.user_id)
        
        ores = {"Stone": 15, "Iron": 60, "Gold": 300, "Diamond": 1500}
        found = random.choices(list(ores.keys()), weights=[60, 25, 10, 5])[0]
        
        # Pickaxe Bonus
        bonus = 2.0 if "Iron_Pickaxe" in data["inventory"] else 1.0
        reward = int(ores[found] * data["multi"] * bonus)
        
        data["points"] += reward
        save_data(economy)
        await interaction.response.send_message(f"⛏️ **{found}**! You earned **{reward:,}** points.", ephemeral=True)

    @discord.ui.button(label="🎣 Fish", style=discord.ButtonStyle.primary, row=0)
    async def fish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        data = get_profile(self.user_id)
        
        fish_types = {"👞 Boot": 5, "🐟 Bass": 40, "🐠 Tropical": 120, "🦈 Shark": 800}
        caught = random.choices(list(fish_types.keys()), weights=[30, 50, 15, 5])[0]
        
        reward = int(fish_types[caught] * data["multi"])
        data["points"] += reward
        data["fish_caught"] += 1
        save_data(economy)
        await interaction.response.send_message(f"🎣 Caught a **{caught}**! Earned **{reward:,}** points.", ephemeral=True)

    @discord.ui.button(label="🛒 Shop", style=discord.ButtonStyle.gray, row=1)
    async def shop_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "**AVAILABLE ITEMS:**\n"
        for name, info in ITEMS.items():
            msg += f"• `{name}`: {info['cost']} pts - *{info['desc']}*\n"
        await interaction.response.send_message(msg, ephemeral=True)

# --- 4. MULTIPLAYER CASINO ---

class BlackjackView(discord.ui.View):
    def __init__(self, ctx, bet):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bet = bet
        self.user_hand = [random.randint(2, 11), random.randint(2, 11)]
        self.dealer_hand = [random.randint(2, 11), random.randint(2, 11)]

    def score(self, hand):
        s = sum(hand)
        if s > 21 and 11 in hand:
            hand[hand.index(11)] = 1
            return sum(hand)
        return s

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.user_hand.append(random.randint(2, 11))
        if self.score(self.user_hand) > 21:
            await self.finish(interaction, "❌ BUSTED!")
        else:
            await self.update(interaction)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        while self.score(self.dealer_hand) < 17:
            self.dealer_hand.append(random.randint(2, 11))
        
        u = self.score(self.user_hand)
        d = self.score(self.dealer_hand)
        prof = get_profile(self.ctx.author.id)

        if d > 21 or u > d:
            msg = f"🏆 WIN! +{self.bet*2}"
            prof["points"] += self.bet * 2
        elif u < d:
            msg = "💀 LOSE!"
        else:
            msg = "⚖️ PUSH!"
            prof["points"] += self.bet
        
        save_data(economy)
        await self.finish(interaction, msg)

    async def update(self, interaction):
        emb = discord.Embed(title="🃏 Blackjack", description=f"Score: {self.score(self.user_hand)}")
        await interaction.response.edit_message(embed=emb)

    async def finish(self, interaction, res):
        emb = discord.Embed(title="🃏 Game Results", description=f"**{res}**\n\nUser: {self.user_hand}\nDealer: {self.dealer_hand}")
        await interaction.response.edit_message(embed=emb, view=None)

# --- 5. CORE COMMANDS ---

@bot.command()
async def hub(ctx):
    data = get_profile(ctx.author.id)
    embed = discord.Embed(title=f"🏰 {ctx.author.name}'s Empire Hub", color=0x2f3136)
    embed.add_field(name="💰 Points", value=f"{data['points']:,}", inline=True)
    embed.add_field(name="⭐ Level", value=data["level"], inline=True)
    embed.add_field(name="🛡️ Shields", value=data["shields"], inline=True)
    
    view = EmpireHubView(ctx.author.id)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def buy(ctx, item_name: str):
    data = get_profile(ctx.author.id)
    if item_name not in ITEMS:
        return await ctx.send("❌ That item isn't in the shop!")
    
    cost = ITEMS[item_name]["cost"]
    if data["points"] < cost:
        return await ctx.send("❌ You cannot afford this!")
    
    data["points"] -= cost
    if ITEMS[item_name]["type"] == "tool":
        data["inventory"].append(item_name)
    elif item_name == "Shield_Battery":
        data["shields"] += 1
        
    save_data(economy)
    await ctx.send(f"✅ Successfully bought **{item_name}**!")

@bot.command()
async def hunt(ctx):
    data = get_profile(ctx.author.id)
    if "Hunting_Rifle" not in data["inventory"]:
        return await ctx.send("❌ You need to buy a `Hunting_Rifle` first!")
    
    animals = {"🐇 Rabbit": 100, "🦌 Deer": 400, "🐻 Bear": 1200, "🐉 Dragon": 5000}
    found = random.choices(list(animals.keys()), weights=[50, 30, 15, 5])[0]
    
    reward = int(animals[found] * data["multi"])
    data["points"] += reward
    data["animals_hunted"] += 1
    save_data(economy)
    await ctx.send(f"🌲 You went into the woods and hunted a **{found}**! +{reward:,} pts")

@bot.command()
async def top(ctx):
    sorted_p = sorted(economy.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
    desc = ""
    for i, (uid, d) in enumerate(sorted_p):
        desc += f"**#{i+1}** <@{uid}> - {d['points']:,} pts\n"
    await ctx.send(embed=discord.Embed(title="🏆 Global Wealth", description=desc))

@bot.command()
async def rob(ctx, target: discord.Member):
    if target.id == ctx.author.id: return
    atk = get_profile(ctx.author.id)
    vic = get_profile(target.id)
    
    if vic["shields"] > 0:
        vic["shields"] -= 1
        atk["points"] -= 1000
        save_data(economy)
        return await ctx.send(f"🛡️ {target.name}'s shield broke! You were fined 1k.")
    
    if random.random() < 0.35:
        stolen = int(vic["points"] * 0.2)
        vic["points"] -= stolen
        atk["points"] += stolen
        await ctx.send(f"🥷 **SUCCESS!** Stole **{stolen:,}** points!")
    else:
        await ctx.send("🚓 **BUSTED!** You fled the scene.")
    save_data(economy)

# --- 6. ADMIN SYSTEM ---

@bot.command()
@commands.has_permissions(administrator=True)
async def give_points(ctx, target: discord.Member, amount: int):
    data = get_profile(target.id)
    data["points"] += amount
    save_data(economy)
    await ctx.send(f"💳 Added **{amount:,}** to {target.name}'s balance.")

# --- 7. AUTOMATION & READY ---

@tasks.loop(hours=1)
async def hourly_bonus():
    # Passive income for everyone online
    for uid in economy:
        economy[uid]["points"] += 100
    save_data(economy)

@bot.event
async def on_ready():
    hourly_bonus.start()
    print(f"🔥 {bot.user.name} IS LIVE (600+ LOGIC ENGINE)")

# ----------------------------------------------------------------
# TOKEN: RESET IN DEV PORTAL AND PASTE BELOW
# ----------------------------------------------------------------
bot.run('PASTE_NEW_TOKEN_HERE')
