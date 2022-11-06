import helpers
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

project_path = os.getenv("PROJECT_PATH")

intents = discord.Intents().all()
bot = commands.Bot(command_prefix = os.getenv("PREFIX"), intents=intents)


"""
def get_cogs():
    # list all cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            yield f"cogs.{filename[:-3]}"


def edit_cog(func, cog, action):
    # perform the selected function on the selected cog
    try:
        func(cog)
    except Exception as e:
        return e
    else:
        return f"{action.capitalize()}ed {cog}"


@bot.command()
@commands.check(helpers.perms_ten)
async def load(ctx, cog=None):
    # loads cogs
    if not cog:
        for cog in get_cogs():
            await ctx.send(edit_cog(bot.load_extension, cog, "load"))
    else:
        await ctx.send(edit_cog(bot.load_extension, cog, "load"))


@bot.command()
@commands.check(helpers.perms_ten)
async def unload(ctx, cog=None):
    # unloads cogs
    if not cog:
        for cog in get_cogs():
            await ctx.send(edit_cog(bot.unload_extension, cog, "unload"))
    else:
        await ctx.send(edit_cog(bot.unload_extension, cog, "unload"))


@bot.command()
@commands.check(helpers.perms_ten)
async def reload(ctx, cog=None):
    # reloads cogs
    if not cog:
        for cog in get_cogs():
            await ctx.send(edit_cog(bot.reload_extension, cog, "reload"))
    else:
        await ctx.send(edit_cog(bot.reload_extension, cog, "reload"))
"""

@bot.command()
async def color(ctx, hex_code=None):
    if not hex_code:
        embed = discord.Embed(title=f"{ctx.author.color}", color=ctx.author.color)
        await ctx.send(embed=embed)
    else:
        str_code = hex_code
        hex_code = int(hex(int(hex_code.replace("#", ''), 16)), 0)
        embed = discord.Embed(title=f"#{str_code}", color=hex_code)
        await ctx.send(embed=embed)
    


@bot.command()
async def online(ctx):
    # command to test if bot is running
    await ctx.send(f"Bot is online with latency {round(bot.latency, 3)}")


@bot.event
async def on_command_error(ctx, error):
    # argument errors are handled function-specifically
    if isinstance(error, commands.MissingRequiredArgument):
        pass
    # missing permissions
    elif isinstance(error,commands.CheckFailure):
        await ctx.send("Check failed (missing permissions)")
    # command does not exist
    elif isinstance(error,commands.CommandNotFound):
        pass
    # any others
    else:
        await ctx.send(error)


@bot.event
async def on_ready():
    os.environ['API_URL'] = 'http://127.0.0.1:5000'
    print(f"{bot.user.name} is online")
    print("-----")
    # set bot activity to help command
    game = discord.Game(os.getenv("ACTIVITY"))
    await bot.change_presence(activity=game)
    # create permissions table
    create_permissions_table = """
        CREATE TABLE IF NOT EXISTS permissions (
            role_id INTEGER PRIMARY KEY,
            permission_level INTEGER NOT NULL
        );
    """
    helpers.execute_query(create_permissions_table)
    # create keys table
    create_keys_table = """
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            owner TEXT,
            alliance_id INTEGER,
            alliance_position INTEGER,
            requests_remaining INTEGER
        );
    """
    helpers.execute_query(create_keys_table)
    # create projects table
    create_projects_table = """
        CREATE TABLE IF NOT EXISTS projects (
            name TEXT PRIMARY KEY,
            description TEXT,
            image_url TEXT,
            cost TEXT
        );
    """
    helpers.execute_query(create_projects_table)
    create_prices_table = """
        CREATE TABLE IF NOT EXISTS prices (
            resource TEXT,
            sell_market INTEGER,
            buy_market INTEGER,
            avg_price INTEGER
        );
    """
    helpers.execute_query(create_prices_table)
  


# load all cogs
print("Loading cogs...")
for filename in os.listdir(project_path + 'cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
        print(f"- {filename}")
print("Done!")



bot.run(os.getenv("BOT_TOKEN"))