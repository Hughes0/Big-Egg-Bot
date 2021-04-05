import helpers
import os
import discord
from discord.ext import commands
from cogs import settings


bot = commands.Bot(command_prefix = "$")



@bot.command()
async def online(ctx):
    # command to test if bot is running
    await ctx.send(f"Bot is online with latency {round(bot.latency, 3)}")


@bot.command()
async def code(ctx):
    total_lines = 0
    for root, dirs, files, in os.walk("."):
        for filename in files:
            if filename.endswith(".py"):
                path = '/'.join([root, filename])
                with open(path, 'r') as f:
                    total_lines += len(f.read().split('\n'))
    await ctx.send(f"{bot.user.name} has {total_lines} lines of code")


@bot.event
async def on_command_error(ctx, error):
    # argument errors are handled function-specifically
    if isinstance(error, commands.MissingRequiredArgument):
        pass
    elif isinstance(error,commands.CheckFailure):
        await ctx.send("Check failed")
    elif isinstance(error,commands.CommandNotFound):
        await ctx.send("Command not found")
    else:
        await ctx.send(error)


@bot.event
async def on_ready():
    print(f"{bot.user.name} is online")
    print("-----")
    # set bot activity to help command
    game = discord.Game(f"{bot.command_prefix}help")
    await bot.change_presence(activity=game)
    # create permissions table
    create_permissions_table = """
    CREATE TABLE IF NOT EXISTS permissions (
        role_id INTEGER PRIMARY KEY,
        permission_level INTEGER NOT NULL
    );
    """
    helpers.execute_query('databases/permissions.sqlite', create_permissions_table)
  


# load all cogs
print("Loading cogs...")
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
        print(f"- {filename}")
print("Done!")



bot.run(helpers.get_data()['token'])