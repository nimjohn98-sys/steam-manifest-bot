import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
DATA_FILE = "points_database.json"
CONFIG_FILE = "server_config.json"

class EconomyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True
        intents.manage_roles = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Register the group
        self.tree.add_command(minigames_group)
        print("🛠️ Minigame commands registered to internal tree.")

    async def on_ready(self):
        print(f'🚀 Logged in as {self.user}')
        try:
            # Force a global sync on startup
            synced = await self.tree.sync()
            print(f"✅ Global Sync: {len(synced)} commands are now live.")
        except Exception as e:
            print(f"❌ Startup Sync Failed: {e}")

bot = EconomyBot()
minigames_group = app_commands.Group(name="minigames", description="All gaming and earning modes")

# ==========================================
# DATABASE UTILITIES
# ==========================================
def get_data(file):
    if not os.path.exists(file): return {}
    with open(file, "r") as f:
        try: return json.load(f)
        except: return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def init_user(db, uid):
    if uid not in db:
        db[uid] = {"points": 100, "messages": 0, "last_daily": None, "last_work": None}
    return db[uid]

# ==========================================
# !SYNC EMERGENCY COMMAND
# ==========================================
@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    """Force command refresh if / is not showing up."""
    await ctx.send("🔄 **Force-syncing...** Please wait.")
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send("✅ Done! If you still don't see `/`, restart Discord (**Ctrl+R**).")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# ==========================================
# 🃏 BLACKJACK SYSTEM
# ==========================================
def calc_hand(hand):
    val, aces = 0, 0
    for c in hand:
        if c['v'] in ['J', 'Q', 'K']: val += 10
        elif c['v'] == 'A': val += 11; aces += 1
        else: val += int(c['v'])
    while val > 21 and aces: val -= 10; aces -= 1
    return val

class BlackjackView(discord.ui.View):
    def __init__(self, interaction, uid, bet):
        super().__init__(timeout=60)
        self.interaction, self.uid, self.bet = interaction, str(uid), bet
        suits, vals = ['♠️', '♥️', '♦️', '♣️'], ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        self.deck = [{'v': v, 's': s} for v in vals for s in suits]
        random.shuffle(self.deck)
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]

    def get_embed(self, done=False):
        p_val = calc_hand(self.player_hand)
        d_val = calc_hand(self.dealer_hand)
        embed = discord.Embed(title="🃏 Blackjack", color=0x2ecc71)
        embed.add_field(name=f"You ({p_val})", value=" ".join([f"[{c['v']}{c['s']}]" for c in self.player_hand]))
        if done:
            embed.add_field(name=f"Dealer ({d_val})", value=" ".join([f"[{c['v']}{c['s']}]" for c in self.dealer_hand]))
        else:
            embed.add_field(name="Dealer (?)", value=f"[{self.dealer_hand[0]['v']}{self.dealer_hand[0]['s']}] [❓]")
        return embed

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        self.player_hand.append(self.deck.pop())
        if calc_hand(self.player_hand) > 21: await self.finish(interaction, "BUST! You lost.")
        else: await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        while calc_hand(self.dealer_hand) < 17: self.dealer_hand.append(self.deck.pop())
        p, d = calc_hand(self.player_hand), calc_hand(self.dealer_hand)
        if d > 21 or p > d: res = "YOU WIN!"
        elif p < d: res = "DEALER WINS."
        else: res = "PUSH (Tie)."
        await self.finish(interaction, res)

    async def finish(self, interaction, res):
        db = get_data(DATA_FILE)
        if "WIN" in res: db[self.uid]["points"] += (self.bet * 2)
        elif "PUSH" in res: db[self.uid]["points"] += self.bet
        save_data(DATA_FILE, db)
        self.stop()
        await interaction.response.edit_message(content=f"**{res}**", embed=self.get_embed(True), view=None)

# ==========================================
# 🕹️ MINIGAMES GROUP COMMANDS
# ==========================================

@minigames_group.command(name="blackjack", description="Play a hand of Blackjack")
async def bj(interaction: discord.Interaction, bet: int):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    if bet <= 0 or user["points"] < bet: return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)
    user["points"] -= bet
    save_data(DATA_FILE, db)
    view = BlackjackView(interaction, interaction.user.id, bet)
    await interaction.response.send_message(embed=view.get_embed(), view=view)

@minigames_group.command(name="slots", description="Spin the slots! (Win up to 10x)")
async def slots(interaction: discord.Interaction, bet: int):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    if bet <= 0 or user["points"] < bet: return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)
    
    emojis = ["🍒", "🍋", "🍇", "💎", "🔔"]
    res = [random.choice(emojis) for _ in range(3)]
    user["points"] -= bet
    
    if res[0] == res[1] == res[2]:
        mult = 10 if res[0] == "💎" else 5
        win = bet * mult
        msg = f"🎰 **JACKPOT!** You won **{win:,}** pts!"
        user["points"] += win
    elif res[0] == res[1] or res[1] == res[2] or res[0] == res[2]:
        win = int(bet * 1.5)
        msg = f"✨ **Mini-Win!** You won **{win:,}** pts!"
        user["points"] += win
    else:
        msg = "💀 Better luck next time."
    
    save_data(DATA_FILE, db)
    await interaction.response.send_message(f"{' | '.join(res)}\n{msg}")

@minigames_group.command(name="coinflip", description="50/50 chance to double points")
async def coinflip(interaction: discord.Interaction, bet: int, side: str):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    if bet <= 0 or user["points"] < bet: return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)
    
    res = random.choice(["heads", "tails"])
    user["points"] -= bet
    if side.lower() == res:
        user["points"] += bet * 2
        msg = f"🪙 It was **{res}**! You doubled your bet."
    else:
        msg = f"🪙 It was **{res}**... You lost."
    
    save_data(DATA_FILE, db)
    await interaction.response.send_message(msg)

@minigames_group.command(name="work", description="Earn a few points safely (1 hour cooldown)")
async def work(interaction: discord.Interaction):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    now = datetime.now()
    
    if user.get("last_work") and now < datetime.fromisoformat(user["last_work"]) + timedelta(hours=1):
        rem = (datetime.fromisoformat(user["last_work"]) + timedelta(hours=1)) - now
        return await interaction.response.send_message(f"⏳ Rest up! You can work again in {int(rem.total_seconds() // 60)} minutes.", ephemeral=True)
    
    pay = random.randint(50, 200)
    jobs = ["Discord Moderator", "Code Bug Fixer", "Pizza Delivery", "Streamer"]
    user["points"] += pay
    user["last_work"] = now.isoformat()
    save_data(DATA_FILE, db)
    await interaction.response.send_message(f"💼 You worked as a **{random.choice(jobs)}** and earned **{pay}** pts!")

@minigames_group.command(name="daily", description="Claim 500 points")
async def daily(interaction: discord.Interaction):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    now = datetime.now()
    if user.get("last_daily") and now < datetime.fromisoformat(user["last_daily"]) + timedelta(days=1):
        return await interaction.response.send_message("⏳ Already claimed today!", ephemeral=True)
    user["points"] += 500
    user["last_daily"] = now.isoformat()
    save_data(DATA_FILE, db)
    await interaction.response.send_message("🎁 **+500 points!**")

@minigames_group.command(name="trivia", description="Answer correctly for 200 points")
async def trivia(interaction: discord.Interaction):
    questions = [
        {"q": "What is the capital of France?", "a": "paris"},
        {"q": "How many legs does a spider have?", "a": "8"},
        {"q": "What is 10 + 15?", "a": "25"}
    ]
    item = random.choice(questions)
    await interaction.response.send_message(f"🧠 **Trivia:** {item['q']} (You have 15s to type the answer!)")

    def check(m): return m.author == interaction.user and m.channel == interaction.channel
    try:
        msg = await bot.wait_for('message', check=check, timeout=15.0)
        if msg.content.lower() == item['a']:
            db = get_data(DATA_FILE)
            init_user(db, str(interaction.user.id))["points"] += 200
            save_data(DATA_FILE, db)
            await interaction.followup.send("✅ Correct! **+200 pts**.")
        else:
            await interaction.followup.send(f"❌ Wrong! The answer was {item['a']}.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ Time's up!")

# --- (Other modes like KOTH and Lottery are kept from previous versions) ---

@minigames_group.command(name="koth", description="Become King for 3x chat earnings")
async def koth(interaction: discord.Interaction):
    db = get_data(DATA_FILE)
    if "koth" not in db: db["koth"] = {"king": None, "price": 1000}
    uid = str(interaction.user.id)
    price = db["koth"]["price"]
    user = init_user(db, uid)
    if user["points"] < price: return await interaction.response.send_message(f"❌ Need {price} pts.", ephemeral=True)
    user["points"] -= price
    db["koth"]["king"] = uid
    db["koth"]["price"] += 500
    save_data(DATA_FILE, db)
    await interaction.response.send_message(f"👑 {interaction.user.mention} is the KING! (3x Multiplier)")

@minigames_group.command(name="lottery", description="Buy ticket (100 pts)")
async def lottery(interaction: discord.Interaction):
    db = get_data(DATA_FILE)
    user = init_user(db, str(interaction.user.id))
    if "lottery" not in db: db["lottery"] = []
    if user["points"] < 100: return await interaction.response.send_message("❌ Need 100 pts.", ephemeral=True)
    user["points"] -= 100
    db["lottery"].append(str(interaction.user.id))
    save_data(DATA_FILE, db)
    await interaction.response.send_message(f"🎟️ Ticket bought! Pot: {len(db['lottery'])*100}")

# ==========================================
# ADMIN & PROFILE
# ==========================================
@bot.tree.command(name="profile", description="Check points")
async def profile(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    db = get_data(DATA_FILE)
    user = init_user(db, str(member.id))
    embed = discord.Embed(title=f"👤 {member.display_name}", description=f"🪙 **{user['points']:,}** points", color=0x3498db)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="shop", description="Browse roles")
async def shop(interaction: discord.Interaction):
    cfg = get_data(CONFIG_FILE)
    embed = discord.Embed(title="🛒 Shop", color=0xf1c40f)
    roles = "".join([f"• <@&{r}>: {i['price']} pts\n" for r, i in cfg.get("roles", {}).items()])
    embed.add_field(name="Roles", value=roles or "None.")
    await interaction.response.send_message(embed=embed)

# ==========================================
# EVENTS
# ==========================================
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    db = get_data(DATA_FILE)
    uid = str(message.author.id)
    user = init_user(db, uid)
    mult = 3 if db.get("koth", {}).get("king") == uid else 1
    user["points"] += (1 * mult)
    save_data(DATA_FILE, db)
    await bot.process_commands(message)

bot.run(TOKEN)
