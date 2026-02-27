import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.command()
async def gen(ctx):
    await ctx.send("Generating something...")

@bot.command()
async def help(ctx):
    await ctx.send("Help command")

@bot.command()
async def list(ctx):
    await ctx.send("Listing items...")

@bot.event
async def on_ready():
    print('Bot is ready!')

bot.run('YOUR_TOKEN_HERE')