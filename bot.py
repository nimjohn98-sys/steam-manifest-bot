import discord
from discord.ext import commands, tasks
import random
import asyncio
import datetime
import json
import os

# --- 1. CORE ENGINE & DB ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "empire_rpg_data.json"

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
            "points": 1000, "multi": 1.0, "rebirths": 0, "shields": 0,
            "job": "Unemployed", "last_daily": None, "inventory": [], 
            "level": 1, "xp": 0, "hp": 100, "max_hp": 100, "class": None,
            "dungeon_wins": 0, "atk": 10, "def": 5
        }
    return economy[uid]

# --- 2. DUNGEON CLASSES ---

class DungeonCombat(discord.ui.View):
    def __init__(self, ctx, player_data, boss_name, boss_hp, reward):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.player_data = player_data
        self.boss_name = boss_name
        self.boss_hp = boss_hp
        self.reward = reward
        self.player_hp = player_data["hp"]

    async def end_game(self, interaction, message):
        save_data(economy)
        await interaction.response.edit_message(content=message, view=None)

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id: return
        
        # Player Turn
        damage = random.randint(self.player_data["atk"] - 2, self.player_data["atk"] + 5)
        self.boss_hp -= damage
        
        if self.boss_hp <= 0:
            self.player_data["points"] += self.reward
            self.player_data["dungeon_wins"] += 1
            self.player_data["xp"] += 50
            return await self.end_game(interaction, f"🏆 **VICTORY!** You slew the {self.boss_name} and looted **{self.reward:,}** points!")

        # Boss Turn
        boss_dmg = max(0, random.randint(10, 20) - self.player_data["def"])
        self.player_hp -= boss_dmg
        
        if self.player_hp <= 0:
            return await self.end_game(interaction, f"💀 **DEFEAT!** The {self.boss_name} struck you down. You lost 200 points to medical bills.")

        await interaction.response.edit_message(content=f"**{self.boss_name} HP:** {self.boss_hp}\n**Your HP:** {self.player_hp}\n\nYou hit for {damage}! Boss hit back for {boss_dmg}!")

# --- 3. MAIN GAME HUB UI ---

class TitanHubView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="⚔️ Dungeon", style=discord.ButtonStyle.danger, row=0)
    async def dungeon_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        data = get_profile(self.user_id)
        
        if data["hp"] <= 20:
            return await interaction.response.send_message("❌ You are too injured! Heal first.", ephemeral=True)
            
        bosses = [("Goblin King", 80, 2000), ("Shadow Dragon", 200, 10000), ("Ancient Golem", 150, 5000)]
        name, hp, reward = random.choice(bosses)
        
        view = DungeonCombat(interaction, data, name, hp, reward)
        await interaction.response.send_message(f"🏰 **Entering Dungeon...** You encountered **{name}**!", view=view)

    @discord.ui.button(label="⚒️ Mine", style=discord.ButtonStyle.blurple, row=0)
    async def mine(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = get_profile(self.user_id)
        reward = int(random.randint(50, 300) * data["multi"])
        data["points"] += reward
        save_data(economy)
        await interaction.response.send_message(f"⛏️ Mined ores worth **{reward}** points!", ephemeral=True)

    @discord.ui.button(label="🏥 Heal (500)", style=discord.ButtonStyle.green, row=1)
    async def heal(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = get_profile(self.user_id)
        if data["points"] < 500:
            return await interaction.response.send_message("❌ Not enough points!", ephemeral=True)
        data["points"] -= 500
        data["hp"] = data["max_hp"]
        save_data(economy)
        await interaction.response.send_message("❤️ Healed to max HP!", ephemeral=True)

# --- 4. COMMANDS ---

@bot.command()
async def hub(ctx):
    data = get_profile(ctx.author.id)
    embed = discord.Embed(title=f"🏰 Titan RPG Hub", color=0xcc0000)
    embed.add_field(name="💰 Points", value=f"{data['points']:,}", inline=True)
    embed.add_field(name="❤️ HP", value=f"{data['hp']}/{data['max_hp']}", inline=True)
    embed.add_field(name="⚔️ ATK/DEF", value=f"{data['atk']}/{data['def']}", inline=True)
    embed.set_footer(text="Join a Dungeon or work for points!")
    await ctx.send(embed=embed, view=TitanHubView(ctx.author.id))

@bot.command()
async def set_class(ctx, choice: str):
    data = get_profile(ctx.author.id)
    if data["class"]: return await ctx.send("❌ You already have a class!")
    
    choice = choice.lower()
    if choice == "warrior":
        data["class"], data["atk"], data["def"] = "Warrior", 15, 10
    elif choice == "mage":
        data["class"], data["atk"], data["def"] = "Mage", 25, 2
    else:
        return await ctx.send("❌ Choose: `!set_class warrior` or `!set_class mage`")
        
    save_data(economy)
    await ctx.send(f"⚔️ You are now a **{data['class']}**!")

@bot.command()
async def rob(ctx, target: discord.Member):
    atk = get_profile(ctx.author.id)
    vic = get_profile(target.id)
    if vic["shields"] > 0:
        vic["shields"] -= 1
        return await ctx.send("🛡️ Shield blocked!")
    
    if random.random() < 0.3:
        stolen = int(vic["points"] * 0.15)
        vic["points"] -= stolen
        atk["points"] += stolen
        await ctx.send(f"🥷 Stole **{stolen}** points!")
    else:
        await ctx.send("👮 Busted!")
    save_data(economy)

@bot.command()
async def top(ctx):
    sorted_db = sorted(economy.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
    desc = "\n".join([f"**#{i+1}** <@{u}>: {d['points']:,}" for i, (u, d) in enumerate(sorted_db)])
    await ctx.send(embed=discord.Embed(title="🏆 Global Wealth", description=desc))

# --- 5. INITIALIZATION ---

@bot.event
async def on_ready():
    print(f"🔥 SYSTEM ACTIVE: {bot.user.name}")

# --- TOKEN ---
# RESET YOUR TOKEN IN THE PORTAL AND PASTE IT BELOW
bot.run('PASTE_YOUR_NEW_TOKEN_HERE')
