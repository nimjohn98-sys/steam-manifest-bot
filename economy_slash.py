import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random

# --- CONFIG ---
TOKEN = 'MTQ3NjYwNTAxMDUwMTQzOTU0OA.GKeB4T.7DZq4z7p56d3CxnJRzM4AQ8fMWmtp8LCkdM2yg'
DATA_FILE = "points_database.json"
CONFIG_FILE = "server_config.json"

class EconomyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.manage_roles = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Slash Commands Synced")

bot = EconomyBot()

# --- DATA HELPERS ---
def get_data(file):
    if not os.path.exists(file): return {}
    with open(file, "r") as f:
        try: return json.load(f)
        except: return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# --- SETUP COMMAND ---
@bot.tree.command(name="setup", description="[ADMIN] Configure shop prices and roles")
@app_commands.describe(
    item="What are you setting up?",
    price="The price for this item",
    role="The role (only if setting up a role item)"
)
@app_commands.choices(item=[
    app_commands.Choice(name="Custom Name Color", value="custom_color"),
    app_commands.Choice(name="Custom Role Name", value="custom_role"),
    app_commands.Choice(name="Add Specific Role to Shop", value="add_role")
])
@commands.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction, item: app_commands.Choice[str], price: int, role: discord.Role = None):
    config = get_data(CONFIG_FILE)
    
    if item.value == "add_role":
        if not role:
            return await interaction.response.send_message("❌ You must select a role to add it to the shop!", ephemeral=True)
        if "roles" not in config: config["roles"] = {}
        config["roles"][str(role.id)] = {"name": role.name, "price": price}
        msg = f"✅ Added **{role.name}** to shop for **{price:,}** pts."
    else:
        config[item.value] = price
        msg = f"✅ Set price for **{item.name}** to **{price:,}** pts."

    save_data(CONFIG_FILE, config)
    await interaction.response.send_message(msg)

# --- SHOP COMMAND ---
@bot.tree.command(name="shop", description="Buy roles and custom perks")
async def shop(interaction: discord.Interaction):
    config = get_data(CONFIG_FILE)
    embed = discord.Embed(title="🛒 Server Shop", color=0xf1c40f)
    
    # Custom Perks
    color_p = config.get("custom_color", 5000)
    role_p = config.get("custom_role", 20000)
    embed.add_field(name="🎨 Custom Perks", value=f"• `/buy_color`: **{color_p:,}** pts\n• `/buy_custom_role`: **{role_p:,}** pts", inline=False)

    # Roles
    roles_list = ""
    for r_id, info in config.get("roles", {}).items():
        roles_list += f"• <@&{r_id}>: **{info['price']:,}** pts\n"
    
    embed.add_field(name="📜 Roles", value=roles_list or "No roles added yet.", inline=False)
    await interaction.response.send_message(embed=embed)

# --- MINIGAMES MENU ---
@bot.tree.command(name="minigames", description="View all ways to earn points")
async def minigames(interaction: discord.Interaction):
    embed = discord.Embed(title="🎮 Minigames & Earning", color=0x3498db)
    embed.add_field(name="🎲 Gambling", value="• `/rps [bet]`: Rock Paper Scissors\n• `/slots [bet]`: Try your luck\n• `/roulette [color] [bet]`: Roulette wheel", inline=False)
    embed.add_field(name="⚒️ Daily & Work", value="• `/daily`: Claim 500 pts (24h)\n• `/work`: Earn random pts (10m cooldown)", inline=False)
    embed.add_field(name="💬 Chatting", value="• Earn **1 point** for every message sent!", inline=False)
    await interaction.response.send_message(embed=embed)

# --- BUY LOGIC (COLOR) ---
@bot.tree.command(name="buy_color", description="Buy a custom name color")
async def buy_color(interaction: discord.Interaction, hex_code: str):
    config = get_data(CONFIG_FILE)
    pts_db = get_data(DATA_FILE)
    cost = config.get("custom_color", 5000)
    uid = str(interaction.user.id)
    
    user_pts = pts_db.get(uid, {}).get("points", 0)
    if user_pts < cost:
        return await interaction.response.send_message(f"❌ You need {cost:,} points!", ephemeral=True)

    try:
        color_val = int(hex_code.lstrip('#'), 16)
        color = discord.Color(color_val)
    except:
        return await interaction.response.send_message("❌ Invalid hex (Example: #ff0000)", ephemeral=True)

    # Deduction
    pts_db[uid]["points"] -= cost
    save_data(DATA_FILE, pts_db)

    # Role Management
    role_name = f"Color-{uid}"
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if role:
        await role.edit(color=color)
    else:
        role = await interaction.guild.create_role(name=role_name, color=color)
        await interaction.user.add_roles(role)
    
    await interaction.response.send_message(f"🎨 Color updated to **{hex_code}**!")

# --- MESSAGE COUNTER ---
@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None: return
    db = get_data(DATA_FILE)
    uid = str(message.author.id)
    if uid not in db: db[uid] = {"points": 0, "messages": 0}
    db[uid]["points"] += 1
    db[uid]["messages"] += 1
    save_data(DATA_FILE, db)
    await bot.process_commands(message)

bot.run(TOKEN)
