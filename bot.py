import discord
from discord import app_commands
from discord.ext import commands
import json, os, random, asyncio
from datetime import datetime, timedelta

# ==========================================
# CONFIG & DATABASE
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
DATA_FILE = "titan_economy.json"

def get_db():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f: 
            json.dump({"users": {}, "global": {"jackpot": 0, "king": None}}, f)
    with open(DATA_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

def init_user(db, uid):
    if uid not in db["users"]:
        db["users"][uid] = {
            "points": 2000, "prestige": 0, "games_played": 0,
            "luck_boost_until": None, "chat_boost_until": None, "tax_shield_until": None,
            "luck_power": 0.0, "multiplier": 1.0
        }
    return db["users"][uid]

# ==========================================
# 🛒 THE SHOP & HUB SYSTEM
# ==========================================
class ShopView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = str(user_id)

    async def buy(self, interaction, cost, item_name, boost_type, duration_mins, power=0):
        db = get_db()
        user = init_user(db, self.user_id)
        if user["points"] < cost:
            return await interaction.response.send_message("❌ You can't afford this!", ephemeral=True)
        
        user["points"] -= cost
        expiry = (datetime.now() + timedelta(minutes=duration_mins)).isoformat()
        user[boost_type] = expiry
        if power: user["luck_power"] = power
        
        save_db(db)
        await interaction.response.send_message(f"✅ Purchased **{item_name}**! Active for {duration_mins}m.", ephemeral=True)

    @discord.ui.button(label="🍀 Clover (5k)", style=discord.ButtonStyle.secondary)
    async def clover(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy(interaction, 5000, "Lucky Clover", "luck_boost_until", 30, 0.10)

    @discord.ui.button(label="🎲 Dice (15k)", style=discord.ButtonStyle.secondary)
    async def dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy(interaction, 15000, "Loaded Dice", "luck_boost_until", 30, 0.25)

    @discord.ui.button(label="📢 Megaphone (10k)", style=discord.ButtonStyle.secondary)
    async def megaphone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy(interaction, 10000, "Megaphone", "chat_boost_until", 60)

    @discord.ui.button(label="🛡️ Tax Shield (20k)", style=discord.ButtonStyle.secondary)
    async def shield(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy(interaction, 20000, "Tax Evasion", "tax_shield_until", 60)

class HubView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

    @discord.ui.button(label="⭐ PRESTIGE", style=discord.ButtonStyle.success)
    async def prestige_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id: return
        db = get_db()
        user = init_user(db, self.user_id)
        cost = 100000 * (user["prestige"] + 1)
        
        if user["points"] < cost:
            return await interaction.response.send_message(f"❌ Prestige {user['prestige']+1} costs {cost:,} pts!", ephemeral=True)
        
        user["points"] = 5000
        user["prestige"] += 1
        user["multiplier"] = 1.0 + (user["prestige"] * 0.5)
        save_db(db)
        await interaction.response.send_message(f"🌟 **ASCENDED!** Multiplier: {user['multiplier']}x", ephemeral=True)

    @discord.ui.button(label="🛒 SHOP", style=discord.ButtonStyle.primary)
    async def shop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🏪 **Welcome to the Black Market.** Choose your boost:", view=ShopView(self.user_id), ephemeral=True)

# ==========================================
# 🎲 GAME ENGINE (20 GAMES)
# ==========================================
GAMES = [
    {"n": "Russian Roulette", "m": "Spinning the cylinder...", "w": "Click... Safely paid.", "l": "BANG! Hospital bills took your bet."},
    {"n": "Cyber Heist", "m": "Bypassing firewalls...", "w": "Mainframe drained!", "l": "Trace detected. Assets frozen."},
    {"n": "High-Stakes Poker", "m": "A tense showdown...", "w": "Full House! You win.", "l": "They had a Royal Flush."},
    {"n": "Street Racing", "m": "Injecting Nitrous...", "w": "Victory! Drifted to gold.", "l": "Spun out. Engine totaled."},
    {"n": "Crypto Pump", "m": "Buying the dip...", "w": "To the Moon! 10x.", "l": "Rug pulled. Worthless."},
    {"n": "Underground Fight", "m": "Heavyweight bout...", "w": "KO! Your fighter won.", "l": "Lost by decision."},
    {"n": "Casino Heist", "m": "Drilling the vault...", "w": "Bags of cash secured!", "l": "Alarm tripped. Fled empty."},
    {"n": "Stock Shorting", "m": "Betting against tech...", "w": "Market crash! Rich.", "l": "Short squeeze. Broke."},
    {"n": "Deep Sea Dive", "m": "Finding the wreck...", "w": "Chest of gold found!", "l": "Oxygen leak. Surfaced."},
    {"n": "Identity Theft", "m": "Cloning a card...", "w": "Pin accepted! Cash out.", "l": "Card declined. Run!"},
    {"n": "Lotto Scratch", "m": "Finding 3 stars...", "w": "JACKPOT!", "l": "Try again next time."},
    {"n": "Weapon Deal", "m": "Meeting in the docks...", "w": "Smooth trade. Heavy pay.", "l": "Ambushed by the feds."},
    {"n": "Art Forgery", "m": "Painting a fake...", "w": "Sold to a billionaire!", "l": "Expert found the crack."},
    {"n": "Sword Duel", "m": "Steel clashing...", "w": "Disarmed them! Glory.", "l": "You were bested."},
    {"n": "Volcano Extraction", "m": "Grabbing Magma Gems...", "w": "Safe exit! Rare loot.", "l": "Lava destroyed the gear."},
    {"n": "Horse Race", "m": "Coming up the inside...", "w": "Thunder wins!", "l": "Horse went for a nap."},
    {"n": "Plane Hijack", "m": "Interception...", "w": "Parachuted with gold!", "l": "Jet engines failed."},
    {"n": "Space Salvage", "m": "Towing a derelict...", "w": "Rare alloy found!", "l": "Black hole suction."},
    {"n": "Baccarat", "m": "Banker/Player...", "w": "Natural 9!", "l": "House wins."},
    {"n": "The Big Wheel", "m": "Spinning the colors...", "w": "Hit the Red 50!", "l": "Landed on Zero."}
]

# ==========================================
# BOT LOGIC
# ==========================================
class TitanBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        self.tree.add_command(games_group)

    async def on_ready(self):
        await self.tree.sync()
        print(f"🔥 Titan Bot Online: {self.user}")

bot = TitanBot()
games_group = app_commands.Group(name="play", description="The 20 Gambling Games")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    db = get_db(); user = init_user(db, str(message.author.id))
    
    # Chat Earnings Logic
    base = 10
    if user["chat_boost_until"] and datetime.now() < datetime.fromisoformat(user["chat_boost_until"]):
        base *= 2
    
    user["points"] += base * user.get("multiplier", 1.0)
    save_db(db)
    await bot.process_commands(message)

@games_group.command(name="gamble", description="Play a game (1-20)")
async def gamble(interaction: discord.Interaction, game_id: int, bet: int):
    db = get_db(); uid = str(interaction.user.id); user = init_user(db, uid)
    if bet <= 0 or user["points"] < bet: return await interaction.response.send_message("❌ Balance too low.", ephemeral=True)
    
    # Calculate Luck
    win_chance = 0.45
    if user["luck_boost_until"] and datetime.now() < datetime.fromisoformat(user["luck_boost_until"]):
        win_chance += user.get("luck_power", 0)

    game = GAMES[game_id-1]
    user["points"] -= bet
    user["games_played"] += 1
    await interaction.response.send_message(f"🎲 **{game['n']}**: {game['m']}")
    await asyncio.sleep(2)

    if random.random() < win_chance:
        win = int(bet * 2 * user.get("multiplier", 1.0))
        user["points"] += win
        await interaction.followup.send(f"✅ {game['w']} **+{win:,}** (x{user.get('multiplier', 1.0)})")
    else:
        # Tax logic
        shield = user["tax_shield_until"] and datetime.now() < datetime.fromisoformat(user["tax_shield_until"])
        if not shield:
            tax = bet / 2
            db["global"]["jackpot"] += tax
            if db["global"]["king"]: db["users"][db["global"]["king"]]["points"] += tax
        await interaction.followup.send(f"❌ {game['l']} **-{bet:,}**" + (" (🛡️ Shielded from Tax)" if shield else ""))
    
    save_db(db)

@bot.command(name="hub")
async def hub(ctx):
    db = get_db(); user = init_user(db, str(ctx.author.id))
    embed = discord.Embed(title=f"🏦 {ctx.author.display_name}'s Hub", color=0x2b2d31)
    embed.add_field(name="💰 Points", value=f"**{user['points']:,.0f}**", inline=True)
    embed.add_field(name="⭐ Prestige", value=f"Lvl {user['prestige']} ({user.get('multiplier', 1.0)}x)", inline=True)
    
    # Active Boosts Check
    active = []
    if user["luck_boost_until"] and datetime.now() < datetime.fromisoformat(user["luck_boost_until"]): active.append("🍀 Luck")
    if user["chat_boost_until"] and datetime.now() < datetime.fromisoformat(user["chat_boost_until"]): active.append("📢 Chat")
    if user["tax_shield_until"] and datetime.now() < datetime.fromisoformat(user["tax_shield_until"]): active.append("🛡️ Shield")
    
    embed.add_field(name="✨ Active Boosts", value=", ".join(active) if active else "None", inline=False)
    await ctx.send(embed=embed, view=HubView(ctx.author.id))

@bot.command()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("✅ Synced.")

bot.run(TOKEN)
