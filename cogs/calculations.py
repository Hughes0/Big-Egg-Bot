import discord
from discord.ext import commands
import math




class Calculations(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def range(self, ctx, score):
        try:
            score = float(score.replace(',', ''))
            if score > 25000:
                raise ValueError("Invalid Input")
        except:
            raise ValueError("Invalid Input")
        min_off, max_off = round(score * 0.75, 2), round(score * 1.75, 2)
        min_def, max_def = round(score / 1.75, 2), round(score / 0.75, 2)
        min_spy, max_spy = round(score * 0.4, 2), round(score * 2.5, 2)
        embed = discord.Embed(title=f"{score} ns", description="War Ranges")
        embed.add_field(name="Offensive War Range", value=f"{min_off} - {max_off}", inline=False)
        embed.add_field(name="Defensive War Range", value=f"{min_def} - {max_def}", inline=False)
        embed.add_field(name="Spy Range", value=f"{min_spy} - {max_spy}", inline=False)
        await ctx.send(embed=embed)

    @range.error
    async def range_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}range <score>`")
        

    

def setup(bot):
    bot.add_cog(Calculations(bot))