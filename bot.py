import discord
from discord.ext import commands
import random
import asyncio
import io
from datetime import datetime

# ==========================================
# ⚙️ GLOBAL CONFIG & JACKPOT
# ==========================================
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'

DB = {}
JACKPOT = 1000  # Starting Jackpot

def get_user(uid, name="Unknown"):
    uid = str(uid)
    if uid not in DB:
        DB[uid] = {"points": 1000, "inv": ["Standard License"], "name": name, "prestige": 0}
    return DB[uid]

# ==========================================
# 🎰 BETTING MODAL GATEWAY
# ==========================================
class BetModal(discord.ui.Modal, title='💰 Place Your Bet'):
    amount = discord.ui.TextInput(label='Bet Amount', placeholder='100')

    def __init__(self, game):
        super().__init__()
        self.game = game

    async def on_submit(self, interaction: discord.Interaction):
        try: bet = int(self.amount.value)
        except: return await interaction.response.send_message("❌ Invalid number.", ephemeral=True)
        
        u = get_user(interaction.user.id, interaction.user.name)
        if bet <= 0 or u["points"] < bet: return await interaction.response.send_message("❌ Inadequate funds.", ephemeral=True)
        
        u["points"] -= bet
        global JACKPOT

        # --- ROUTING ---
        if self.game == "coinflip":
            win = random.random() > 0.5
            side = "HEADS" if win else "TAILS"
            if win: u["points"] += bet * 2
            else: JACKPOT += int(bet * 0.1)
            await interaction.response.send_message(f"🪙 It's **{side}**! " + (f"Won {bet*2}!" if win else "Lost bet."))

        elif self.game == "crash":
            view = CrashView(interaction.user.id, bet)
            await interaction.response.send_message(embed=discord.Embed(title="📈 CRASH", description="Preparing..."), view=view)
            msg = await interaction.original_response()
            bot.loop.create_task(view.run(msg))

        elif self.game == "slots":
            icons = ["🍒", "🍋", "🔔", "💎"]
            res = [random.choice(icons) for _ in range(3)]
            win_amt = 0
            if res[0] == res[1] == res[2]:
                if res[0] == "💎": # JACKPOT WIN
                    win_amt = bet * 10 + JACKPOT
                    JACKPOT = 1000
                    msg = f"🎊 **JACKPOT WINNER!** +{win_amt} pts!"
                else: win_amt = bet * 10; msg = f"✅ TRIPLE! +{win_amt} pts"
            elif res[0] == res[1] or res[1] == res[2]:
                win_amt = int(bet * 1.5); msg = f"✅ Double! +{win_amt} pts"
            else:
                JACKPOT += int(bet * 0.1); msg = "❌ Lost."
            u["points"] += win_amt
            await interaction.response.send_message(f"🎰 | {' | '.join(res)} | 🎰\n{msg}")

        elif self.game == "blackjack":
            view = BlackjackView(interaction.user.id, bet)
            await interaction.response.send_message(embed=view.get_embed(), view=view)

# ==========================================
# 🎮 ADVANCED GAME VIEWS (CRASH & BJ)
# ==========================================
class CrashView(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(); self.uid, self.bet, self.m, self.end = uid, bet, 1.0, False
        self.limit = round(random.uniform(1.1, 4.0), 2)

    @discord.ui.button(label="CASH OUT", style=discord.ButtonStyle.green)
    async def stop(self, interaction, b):
        if self.end or interaction.user.id != self.uid: return
        self.end = True
        get_user(self.uid)["points"] += int(self.bet * self.m)
        await interaction.response.edit_message(content=f"💰 Cashed at {self.m}x!", view=None)

    async def run(self, msg):
        while not self.end:
            await asyncio.sleep(1.5)
            self.m = round(self.m + 0.2, 1)
            if self.m >= self.limit:
                self.end = True
                global JACKPOT; JACKPOT += int(self.bet * 0.1)
                await msg.edit(content=f"💥 CRASHED at {self.m}x!", embed=None, view=None)
                break
            await msg.edit(embed=discord.Embed(title=f"📈 Multiplier: {self.m}x", color=0xf1c40f))

class BlackjackView(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(timeout=60); self.uid, self.bet = uid, bet
        self.p = [random.randint(2,11), random.randint(2,11)]
        self.d = [random.randint(2,11), random.randint(2,11)]

    def get_embed(self, final=False):
        e = discord.Embed(title="🃏 Blackjack", color=0x2ecc71)
        e.add_field(name="You", value=f"Total: {sum(self.p)}")
        e.add_field(name="Dealer", value=f"Total: {sum(self.d) if final else '?'}")
        return e

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple)
    async def hit(self, i, b):
        self.p.append(random.randint(2,11))
        if sum(self.p) > 21: await i.response.edit_message(content="💥 BUST!", view=None)
        else: await i.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, i, b):
        while sum(self.d) < 17: self.d.append(random.randint(2,11))
        ps, ds, u = sum(self.p), sum(self.d), get_user(self.uid)
        if ds > 21 or ps > ds: u["points"] += self.bet * 2; res = "✅ WIN!"
        elif ps < ds: res = "❌ LOSE."; global JACKPOT; JACKPOT += int(self.bet * 0.1)
        else: u["points"] += self.bet; res = "🤝 PUSH."
        await i.response.edit_message(content=res, embed=self.get_embed(True), view=None)

# ==========================================
# 🖥️ THE HUB (RE-ORGANIZED)
# ==========================================
class UltimateHub(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="Profile", style=discord.ButtonStyle.gray, row=0)
    async def p(self, i, b):
        u = get_user(i.user.id, i.user.name)
        await i.response.send_message(f"👤 {i.user.name} | Points: {u['points']} | Jackpot: {JACKPOT}", ephemeral=True)

    # GAME ROW 1
    @discord.ui.button(label="Crash", style=discord.ButtonStyle.danger, emoji="📈", row=1)
    async def g1(self, i, b): await i.response.send_modal(BetModal("crash"))
    @discord.ui.button(label="Slots", style=discord.ButtonStyle.danger, emoji="🎰", row=1)
    async def g2(self, i, b): await i.response.send_modal(BetModal("slots"))
    @discord.ui.button(label="Blackjack", style=discord.ButtonStyle.danger, emoji="🃏", row=1)
    async def g3(self, i, b): await i.response.send_modal(BetModal("blackjack"))

    # GAME ROW 2
    @discord.ui.button(label="Coinflip", style=discord.ButtonStyle.danger, emoji="🪙", row=2)
    async def g4(self, i, b): await i.response.send_modal(BetModal("coinflip"))
    @discord.ui.button(label="Dice", style=discord.ButtonStyle.danger, emoji="🎲", row=2)
    async def g5(self, i, b): await i.response.send_modal(BetModal("dice"))

# ==========================================
# 🚀 LAUNCH
# ==========================================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_message(message):
    if not message.author.bot: get_user(message.author.id, message.author.name)["points"] += 1
    await bot.process_commands(message)

@bot.command()
async def hub(ctx): await ctx.send("🌐 **Steam Hub v11**", view=UltimateHub())

@bot.event
async def on_ready(): print(f"✅ V11 Ready: {bot.user}")

bot.run(TOKEN)
