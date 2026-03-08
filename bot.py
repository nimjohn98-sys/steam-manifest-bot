import discord
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
DATA_FILE = "steam_data.json"

class SteamBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def on_ready(self):
        print(f'🚀 STEAM ENGINE ONLINE: {self.user}')
        print('>> Type !steam to open the Dashboard.')

bot = SteamBot()

# ==========================================
# DATA SYSTEM (The Manifest)
# ==========================================
def load_db():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(uid):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {
            "points": 2500,
            "inventory": ["Welcome Badge"],
            "stats": {"wins": 0, "losses": 0, "total_bet": 0},
            "last_daily": None
        }
        save_db(db)
    return db[uid]

def update_user(uid, data):
    db = load_db()
    db[str(uid)] = data
    save_db(db)

# ==========================================
# ADVANCED GUI - BLACKJACK
# ==========================================
class BlackjackGUI(discord.ui.View):
    def __init__(self, ctx, bet):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bet = bet
        self.deck = [v for v in ['2','3','4','5','6','7','8','9','10','J','Q','K','A'] for _ in range(4)]
        random.shuffle(self.deck)
        self.player = [self.deck.pop(), self.deck.pop()]
        self.dealer = [self.deck.pop(), self.deck.pop()]

    def get_score(self, hand):
        val, aces = 0, 0
        for card in hand:
            if card in ['J','Q','K']: val += 10
            elif card == 'A': val += 11; aces += 1
            else: val += int(card)
        while val > 21 and aces: val -= 10; aces -= 1
        return val

    def create_embed(self, closed=True):
        embed = discord.Embed(title="🃏 Steam Blackjack", color=0x1b2838)
        embed.add_field(name="Your Hand", value=f"{' '.join(self.player)}\nScore: {self.get_score(self.player)}", inline=True)
        dealer_display = f"{self.dealer[0]} ❓" if closed else f"{' '.join(self.dealer)}\nScore: {self.get_score(self.dealer)}"
        embed.add_field(name="Dealer", value=dealer_display, inline=True)
        return embed

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author: return
        self.player.append(self.deck.pop())
        if self.get_score(self.player) > 21:
            await self.finish(interaction, "BUST! Dealer Wins.", False)
        else:
            await interaction.response.edit_message(embed=self.create_embed())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author: return
        while self.get_score(self.dealer) < 17:
            self.dealer.append(self.deck.pop())
        
        p_score = self.get_score(self.player)
        d_score = self.get_score(self.dealer)
        
        if d_score > 21 or p_score > d_score:
            await self.finish(interaction, "YOU WIN!", True)
        elif p_score < d_score:
            await self.finish(interaction, "Dealer Wins.", False)
        else:
            await self.finish(interaction, "PUSH (Tie).", None)

    async def finish(self, interaction, result, won):
        user_data = get_user(self.ctx.author.id)
        if won is True: user_data["points"] += self.bet * 2
        elif won is None: user_data["points"] += self.bet
        update_user(self.ctx.author.id, user_data)
        self.stop()
        await interaction.response.edit_message(content=f"**{result}**", embed=self.create_embed(False), view=None)

# ==========================================
# MAIN DASHBOARD (The Steam Hub)
# ==========================================
class SteamDashboard(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=120)
        self.ctx = ctx

    @discord.ui.button(label="My Profile", style=discord.ButtonStyle.gray, emoji="👤")
    async def profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = get_user(interaction.user.id)
        embed = discord.Embed(title=f"Steam Profile: {interaction.user.display_name}", color=0x66c0f4)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Wallet Balance", value=f"🪙 {user['points']:,} pts", inline=False)
        embed.add_field(name="Manifest (Inventory)", value=", ".join(user['inventory']) or "Empty", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Play Blackjack", style=discord.ButtonStyle.green, emoji="🃏")
    async def play_bj(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = get_user(interaction.user.id)
        if user["points"] < 100:
            return await interaction.response.send_message("❌ Insufficient funds (Min 100).", ephemeral=True)
        user["points"] -= 100
        update_user(interaction.user.id, user)
        view = BlackjackGUI(self.ctx, 100)
        await interaction.response.send_message(embed=view.create_embed(), view=view)

    @discord.ui.button(label="Spin Slots", style=discord.ButtonStyle.blurple, emoji="🎰")
    async def play_slots(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = get_user(interaction.user.id)
        if user["points"] < 50:
            return await interaction.response.send_message("❌ Insufficient funds (Min 50).", ephemeral=True)
        
        user["points"] -= 50
        icons = ["💎", "🍒", "🍋", "🔔", "⭐"]
        res = [random.choice(icons) for _ in range(3)]
        
        win = 0
        if res[0] == res[1] == res[2]: win = 1000 if res[0] == "💎" else 500
        elif res[0] == res[1] or res[1] == res[2]: win = 100
        
        user["points"] += win
        update_user(interaction.user.id, user)
        result_text = f"🎰 **{' | '.join(res)}** 🎰\n" + (f"✅ You won **{win}**!" if win > 0 else "❌ No luck.")
        await interaction.response.send_message(result_text)

    @discord.ui.button(label="Claim Daily", style=discord.ButtonStyle.primary, emoji="🎁")
    async def daily(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = get_user(interaction.user.id)
        now = datetime.now()
        if user["last_daily"] and now < datetime.fromisoformat(user["last_daily"]) + timedelta(days=1):
            return await interaction.response.send_message("⏳ Already claimed! Come back later.", ephemeral=True)
        
        user["points"] += 500
        user["last_daily"] = now.isoformat()
        update_user(interaction.user.id, user)
        await interaction.response.send_message("🎁 **+500 points** added to your Steam Wallet!")

# ==========================================
# COMMANDS
# ==========================================
@bot.command()
async def steam(ctx):
    """Opens the Steam Dashboard GUI"""
    embed = discord.Embed(
        title="🎮 Steam Gaming Manifest",
        description="Welcome to the digital library. Manage your inventory and gamble your wallet points below.",
        color=0x171a21
    )
    embed.set_image(url="https://i.imgur.com/vH9Yn2P.png") # Steam-like header
    await ctx.send(embed=embed, view=SteamDashboard(ctx))

@bot.command()
@commands.has_permissions(administrator=True)
async def give_points(ctx, member: discord.Member, amount: int):
    user = get_user(member.id)
    user["points"] += amount
    update_user(member.id, user)
    await ctx.send(f"✅ Transferred **{amount:,}** points to {member.mention}'s Wallet.")

@bot.event
async def on_message(message):
    if message.author.bot: return
    # Passive chat earning
    user = get_user(message.author.id)
    user["points"] += 2 
    update_user(message.author.id, user)
    await bot.process_commands(message)

bot.run(TOKEN)
