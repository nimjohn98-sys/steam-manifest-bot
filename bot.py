import discord
from discord.ext import commands
import random
import asyncio
import io
from datetime import datetime, timedelta

# ==========================================
# ⚙️ CONFIG & TOKEN
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
MANIFEST_COST = 40
DAILY_AMOUNT = 500

# Memory-based Storage
DB = {}

def get_user(uid):
    uid = str(uid)
    if uid not in DB:
        DB[uid] = {
            "points": 1000, 
            "inv": ["Steam License v1.0"], 
            "xp": 0, 
            "last_daily": None,
            "wins": 0
        }
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

        # Deduct bet upfront
        user["points"] -= bet
        
        if self.game_key == "blackjack":
            view = BlackjackGame(interaction.user.id, bet)
            await interaction.response.send_message(embed=view.get_embed(), view=view)
        
        elif self.game_key == "slots":
            icons = ["💎", "🍒", "🍋", "🔔", "⭐"]
            res = [random.choice(icons) for _ in range(3)]
            win_amt = 0
            if res[0] == res[1] == res[2]:
                win_amt = bet * 10 if res[0] == "💎" else bet * 5
            elif res[0] == res[1] or res[1] == res[2]:
                win_amt = int(bet * 1.5)
            
            user["points"] += win_amt
            if win_amt > 0: user["wins"] += 1
            
            await interaction.response.send_message(f"🎰 | {' | '.join(res)} | 🎰\n" + (f"✅ **WIN! +{win_amt} pts**" if win_amt > 0 else "❌ **LOST**"))

        elif self.game_key == "coinflip":
            outcome = random.choice(["Heads", "Tails"])
            win = random.random() > 0.5
            if win:
                user["points"] += bet * 2
                user["wins"] += 1
            await interaction.response.send_message(f"🪙 **{outcome}**! " + (f"Won **{bet*2}** pts!" if win else "Lost bet."))

        elif self.game_key == "crash":
            view = CrashGame(interaction.user.id, bet)
            await interaction.response.send_message(embed=discord.Embed(title="📈 CRASH", description="Starting...", color=0xf1c40f), view=view)
            msg = await interaction.original_response()
            bot.loop.create_task(view.run(msg))

# ==========================================
# 🎮 GAME ENGINES
# ==========================================

class BlackjackGame(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(timeout=60)
        self.uid, self.bet = str(uid), bet
        cards = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        self.p_hand = [random.choice(cards), random.choice(cards)]
        self.d_hand = [random.choice(cards), random.choice(cards)]

    def score(self, hand):
        val, aces = 0, 0
        for c in hand:
            if c in ['J','Q','K']: val += 10
            elif c == 'A': val += 11; aces += 1
            else: val += int(c)
        while val > 21 and aces: val -= 10; aces -= 1
        return val

    def get_embed(self, final=False):
        e = discord.Embed(title="🃏 Blackjack", color=0x2ecc71)
        e.add_field(name="Your Hand", value=f"{' '.join(self.p_hand)} (`{self.score(self.p_hand)}`)")
        d_val = self.score(self.d_hand) if final else "?"
        d_cards = ' '.join(self.d_hand) if final else f"{self.d_hand[0]} ❓"
        e.add_field(name="Dealer", value=f"{d_cards} (`{d_val}`)")
        return e

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple)
    async def hit(self, interaction: discord.Interaction, b: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        self.p_hand.append(random.choice(['2','3','4','5','6','7','8','9','10','J','Q','K','A']))
        if self.score(self.p_hand) > 21:
            await interaction.response.edit_message(content="💥 BUST!", embed=self.get_embed(True), view=None)
        else:
            await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, b: discord.ui.Button):
        if str(interaction.user.id) != self.uid: return
        while self.score(self.d_hand) < 17: self.d_hand.append(random.choice(['2','3','4','5','6','7','8','9','10','J','Q','K','A']))
        ps, ds = self.score(self.p_hand), self.score(self.d_hand)
        
        user = get_user(self.uid)
        if ds > 21 or ps > ds:
            res = "✅ **YOU WON!**"
            user["points"] += self.bet * 2
            user["wins"] += 1
        elif ps < ds:
            res = "❌ **DEALER WINS.**"
        else:
            res = "🤝 **PUSH (TIE).**"
            user["points"] += self.bet
            
        await interaction.response.edit_message(content=res, embed=self.get_embed(True), view=None)

class CrashGame(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(timeout=None)
        self.uid, self.bet, self.m, self.end = str(uid), bet, 1.0, False
        self.boom = round(random.uniform(1.1, 3.8), 2)

    @discord.ui.button(label="CASH OUT", style=discord.ButtonStyle.green)
    async def stop(self, interaction: discord.Interaction, b: discord.ui.Button):
        if self.end or str(interaction.user.id) != self.uid: return
        self.end = True
        user = get_user(self.uid)
        winnings = int(self.bet * self.m)
        user["points"] += winnings
        user["wins"] += 1
        await interaction.response.edit_message(content=f"💰 Cashed at **{self.m}x**! Won **{winnings}** pts.", embed=None, view=None)

    async def run(self, msg):
        while not self.end:
            await asyncio.sleep(1.5)
            self.m = round(self.m + 0.2, 1)
            if self.m >= self.boom:
                self.end = True
                await msg.edit(content=f"💥 **CRASHED at {self.m}x!** You lost your bet.", embed=None, view=None)
                break
            await msg.edit(embed=discord.Embed(title=f"📈 Multiplier: {self.m}x", description="Click 'Cash Out' before it crashes!", color=0xf1c40f))

# ==========================================
# 🖥️ THE MODULAR HUB
# ==========================================
class UltimateHub(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Profile", style=discord.ButtonStyle.secondary, emoji="👤", row=0)
    async def profile(self, interaction: discord.Interaction, b: discord.ui.Button):
        u = get_user(interaction.user.id)
        e = discord.Embed(title=f"👤 {interaction.user.display_name}'s Profile", color=0x3498db)
        e.add_field(name="Wallet", value=f"🪙 {u['points']} pts")
        e.add_field(name="Total Wins", value=f"🏆 {u['wins']}")
        e.add_field(name="Inventory", value=f"📦 {', '.join(u['inv'])}")
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="Daily +500", style=discord.ButtonStyle.success, emoji="🎁", row=0)
    async def daily(self, interaction: discord.Interaction, b: discord.ui.Button):
        u = get_user(interaction.user.id)
        now = datetime.now()
        
        if u["last_daily"]:
            last = datetime.fromisoformat(u["last_daily"])
            if now < last + timedelta(days=1):
                wait = (last + timedelta(days=1)) - now
                return await interaction.response.send_message(f"⏳ Too early! Come back in **{wait.seconds//3600}h {(wait.seconds//60)%60}m**.", ephemeral=True)
        
        u["points"] += DAILY_AMOUNT
        u["last_daily"] = now.isoformat()
        await interaction.response.send_message(f"🎁 **{DAILY_AMOUNT}** points added! See you tomorrow.", ephemeral=True)

    @discord.ui.button(label="Manifest (40 pts)", style=discord.ButtonStyle.primary, emoji="💾", row=0)
    async def manifest(self, interaction: discord.Interaction, b: discord.ui.Button):
        u = get_user(interaction.user.id)
        if u["points"] < MANIFEST_COST:
            return await interaction.response.send_message("❌ Need 40 pts.", ephemeral=True)
        
        u["points"] -= MANIFEST_COST
        
        # 1. THE OLD STYLE EMBED
        e = discord.Embed(title="📟 Steam System Manifest", color=0x1b2838)
        e.add_field(name="User", value=interaction.user.name, inline=True)
        e.add_field(name="Wallet Status", value=f"{u['points']} pts", inline=True)
        e.add_field(name="Software Library", value="\n".join(u['inv']), inline=False)
        e.set_footer(text=f"Auth ID: {random.randint(10000, 99999)}")

        # 2. THE FILE GENERATION
        log = f"SERIAL: {random.getrandbits(32)}\nUSER: {interaction.user}\nPOINTS: {u['points']}\nDATE: {datetime.now()}"
        file = discord.File(fp=io.BytesIO(log.encode()), filename="manifest.txt")
        
        await interaction.response.send_message(content="✅ Manifest Compiled:", embed=e, file=file)

    @discord.ui.button(label="Blackjack", style=discord.ButtonStyle.danger, row=1)
    async def bj(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(BetWindow("blackjack"))

    @discord.ui.button(label="Crash", style=discord.ButtonStyle.danger, row=1)
    async def cr(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(BetWindow("crash"))

    @discord.ui.button(label="Slots", style=discord.ButtonStyle.danger, row=1)
    async def sl(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(BetWindow("slots"))

    @discord.ui.button(label="Coinflip", style=discord.ButtonStyle.danger, row=1)
    async def cf(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(BetWindow("coinflip"))

# ==========================================
# 🚀 INITIALIZE
# ==========================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.command()
async def hub(ctx):
    embed = discord.Embed(title="🌐 Steam Global Hub", description="Manage your profile or play games below.", color=0x1b2838)
    await ctx.send(embed=embed, view=UltimateHub())

@bot.event
async def on_ready():
    print(f"✅ V4 Online: {bot.user}")

bot.run(TOKEN)
