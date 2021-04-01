import helpers
import os
import discord
from discord.ext import commands


bot = commands.Bot(command_prefix = "$")



@bot.command()
async def online(ctx):
    await ctx.send(f"Bot is online with latency {round(bot.latency, 3)}")



@bot.event
async def on_ready():
    print(f"{bot.user.name} is online")
    print("-----")
    # set bot activity to help command
    game = discord.Game(f"{bot.command_prefix}help")
    await bot.change_presence(activity=game)
  


# # load all cogs
# for filename in os.listdir('./cogs'):
#     if filename.endswith('.py'):
#         bot.load_extension(f'cogs.{filename[:-3]}')
#         print(f"Loading cog: {filename}")



bot.run(helpers.get_entry("token"))