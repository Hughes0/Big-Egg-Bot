import discord
from discord.ext import commands
import math




class Calculations(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def range(self, ctx, score):
        try:
            if float(score) > 25000:
                raise ValueError("Invalid Input")
        except:
            raise ValueError("Invalid Input")
        score = float(score.replace(',', ''))
        embed = discord.Embed(title=f"{score} ns", description="War Ranges")
        await ctx.send(embed=embed)

    

def setup(bot):
    bot.add_cog(Calculations(bot))