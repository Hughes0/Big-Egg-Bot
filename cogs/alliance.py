import discord
from discord.ext import commands


class Alliance(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    
    @commands.command()
    async def warchest(self, ctx, cities):
        try:
            cities = int(cities)
        except:
            raise ValueError("Invalid input")
        if cities > 60 or cities < 1:
            raise ValueError("Inputs out of range")
        
    @warchest.error
    async def warchest_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}warchest <cities>`")

    
    @commands.command()
    async def militarization(self, ctx, alliance_id, min_cities=0, max_cities=100):
        try:
            alliance_id = int(alliance_id)
            min_cities = int(max_cities)
            max_cities = int(max_cities)
        except:
            raise ValueError("Invalid input")
        if min_cities > max_cities:
            raise ValueError("min_cities must be greater than max_cities")
        if min_cities < 0 or max_cities < 0 or min_cities > 100 or max_cities > 100:
            raise ValueError("Inputs out of range")

    @militarization.error
    async def militarization_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}militarization <alliance_id> [min_cities] [max_cities]`")