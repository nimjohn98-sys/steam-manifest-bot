import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime

# ==========================================
# ⚙️ CONFIG & DATABASE
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
DB = {}
GLOBAL_JACKPOT = 2500

def get_u(uid, name="User"):
    uid = str(uid)
    if uid not in DB: DB[uid] = {"points": 1000, "inv": [], "name": name}
    return DB[uid]

# ==========================================
# 🎮 THE 20 GAME MODES SELECTOR
# ==========================================
class GameSelector(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Slots", description="Match 3 for Jackpot", emoji="🎰"),
            discord.SelectOption(label="Crash", description="Cash out before the boom", emoji="📈"),
            discord.SelectOption(label="Blackjack", description="Beat the dealer to 21", emoji="🃏"),
            discord.SelectOption(label="Coinflip", description="50/50 Double or Nothing", emoji="🪙"),
            discord.SelectOption(label="Roulette", description="Bet on Red, Black, or Green", emoji="🎡"),
            discord.SelectOption(label="Dice Roll", description="Higher roll wins", emoji="🎲"),
            discord.SelectOption(label="Higher/Lower", description="Guess the next number", emoji="⬆️"),
            discord.SelectOption(label="RPS", description="Rock Paper Scissors", emoji="✂️"),
            discord.SelectOption(label="Mines", description="Avoid the hidden bombs", emoji="💣"),
            discord.SelectOption(label="Towers", description="Climb for multipliers", emoji="🗼"),
            discord.SelectOption(label="Baccarat", description="Bet on Player or Banker", emoji="👑"),
            discord.SelectOption(label="Keno", description="Pick lucky numbers", emoji="🔢"),
            discord.SelectOption(label="Wheel of Fortune", description="Spin for a random prize", emoji="☸️"),
            discord.SelectOption(label="Scratch Card", description="Scratch for instant points", emoji="🎫"),
            discord.SelectOption(label="Horse Racing", description="Bet on the fastest horse", emoji="🐎"),
            discord.SelectOption(label="Plinko", description="Drop the ball for a multi", emoji="🎾"),
            discord.SelectOption(label="Lottery", description="Buy a ticket for the Jackpot", emoji="🎟️"),
            discord.SelectOption(label="Penalty Shootout", description="Score a goal to win", emoji="⚽"),
            discord.SelectOption(label="Diamond Mine", description="Click to find gems", emoji="💎"),
            discord.SelectOption(label="War", description="Highest card wins simple", emoji="⚔️")
        ]
        super().__init__(placeholder="Choose a Game Mode (20 Available)...", options=options)

    async def callback(self, interaction: discord.Interaction):
        game = self.values[0]
        await interaction.response.send_modal(BetModal(game))

# ==========================================
# 💰 THE MULTI-GAME BETTING ENGINE
# ==========================================
class BetModal(discord.ui.Modal, title='Steam Casino'):
    amount = discord.ui.TextInput(label='Enter Bet Amount', placeholder='100')
    def __init__(self, game): super().__init__(); self.game = game

    async def on_submit(self, interaction: discord.Interaction):
        try: bet = int(self.amount.value)
        except: return await interaction.response.send_message("❌ Numbers only!", ephemeral=True)
        
        u = get_u(interaction.user.id, interaction.user.name)
        if bet <= 0 or u["points"] < bet: return await interaction.response.send_message("❌ Poor.", ephemeral=True)
        
        u["points"] -= bet
        global GLOBAL_JACKPOT
        
        # --- GAME LOGIC SAMPLES (Expanding to all 20) ---
        res_msg = ""
        win = False

        if self.game == "Coinflip":
            win = random.random() > 0.5
            res_msg = f"🪙 It landed on **{'HEADS' if win else 'TAILS'}**!"
        
        elif self.game == "Dice Roll":
            p, d = random.randint(1,6), random.randint(1,6)
            win = p > d
            res_msg = f"🎲 You rolled {p}, Dealer rolled {d}."

        elif self.game == "War" or self.game == "Higher/Lower":
            p, d = random.randint(1,13), random.randint(1,13)
            win = p >= d
            res_msg = f"⚔️ Your Card: {p} | Enemy Card: {d}"

        elif self.game == "Wheel of Fortune":
            multi = random.choice([0, 0.5, 1.5, 2, 5])
            u["points"] += int(bet * multi)
            return await interaction.response.send_message(f"☸️ Wheel stopped at **{multi}x**! Result: {int(bet*multi)} pts.")

        elif self.game == "Slots":
            icons = ["🍒", "💎", "🍋"]
            pull = [random.choice(icons) for _ in range(3)]
            if pull[0] == pull[1] == pull[2]:
                win_amt = (bet * 50) + GLOBAL_JACKPOT if pull[0] == "💎" else bet * 10
                u["points"] += win_amt
                GLOBAL_JACKPOT = 2500
                return await interaction.response.send_message(f"🎰 {'|'.join(pull)} 🎰\n🎊 **MEGA WIN! +{win_amt} pts**")
            res_msg = f"🎰 {'|'.join(pull)} 🎰"

        # General Payout Logic
        if win:
            payout = bet * 2
            u["points"] += payout
            await interaction.response.send_message(f"{res_msg}\n✅ **YOU WON {payout} pts!**")
        else:
            GLOBAL_JACKPOT += int(bet * 0.15)
            await interaction.response.send_message(f"{res_msg}\n❌ **YOU LOST.** Jackpot is now: {GLOBAL_JACKPOT}")

# ==========================================
# 🖥️ HUB INTERFACE
# ==========================================
class UltimateHub(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GameSelector())

    @discord.ui.button(label="Profile", style=discord.ButtonStyle.gray, row=1)
    async def profile(self, i, b):
        u = get_u(i.user.id, i.user.name)
        await i.response.send_message(f"👤 {i.user.name}\n🪙 Wallet: {u['points']}\n⭐ Prestige: 0", ephemeral=True)

    @discord.ui.button(label="Leaderboard", style=discord.ButtonStyle.secondary, row=1)
    async def lb(self, i, b):
        top = sorted(DB.items(), key=lambda x: x[1]['points'], reverse=True)[:5]
        board = "\n".join([f"#{idx+1} {v['name']}: {v['points']}" for idx, (k, v) in enumerate(top)])
        await i.response.send_message(f"🏆 **Top Richest**\n{board}", ephemeral=True)

# ==========================================
# 🚀 CORE
# ==========================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_message(msg):
    if not msg.author.bot: get_u(msg.author.id, msg.author.name)["points"] += 1
    await bot.process_commands(msg)

@bot.command()
async def hub(ctx):
    await ctx.send("🌐 **Steam Omni-Hub v13**\nSelect a game below to start playing!", view=UltimateHub())

@bot.event
async def on_ready(): print(f"✅ V13 Online: {bot.user}")

bot.run(TOKEN)
