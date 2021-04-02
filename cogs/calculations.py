import discord
from discord.ext import commands
import math
import random



class Calculations(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot


    @commands.command(brief="War ranges")
    async def range(self, ctx, score):
        try:
            score = float(score.replace(',', ''))
            if score > 25000:
                raise ValueError("Invalid input")
        except:
            raise ValueError("Invalid input")
        min_off, max_off = round(score*0.75, 2), round(score*1.75, 2)
        min_def, max_def = round(score/1.75, 2), round(score/0.75, 2)
        min_spy, max_spy = round(score*0.4, 2), round(score*2.5, 2)
        embed = discord.Embed(title=f"{score} ns", description="War Ranges")
        embed.add_field(name="Offensive War Range", value=f"{min_off} - {max_off}", inline=False)
        embed.add_field(name="Defensive War Range", value=f"{min_def} - {max_def}", inline=False)
        embed.add_field(name="Spy Range", value=f"{min_spy} - {max_spy}", inline=False)
        await ctx.send(embed=embed)

    @range.error
    async def range_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}range <score>`")
        

    @commands.command(brief="Ground battle simulator")
    async def ground(self, ctx, att_soldiers, att_tanks, def_soldiers, def_tanks):
        try:
            att_soldiers = int(att_soldiers.replace(',', ''))
            att_tanks = int(att_tanks.replace(',', ''))
            def_soldiers = int(def_soldiers.replace(',', ''))
            def_tanks = int(def_tanks.replace(',', ''))
        except:
            raise ValueError("Invalid input")
        if att_soldiers > 1000000 or def_soldiers > 1000000 or att_tanks > 100000 or def_tanks > 100000:
            raise ValueError("Values too large")
        att_value = att_soldiers*1.75 + att_tanks*40
        def_value = def_soldiers*1.75 + def_tanks*40
        immense, moderate, pyrrhic, failure = (0, 0, 0, 0)
        for i in range(1000):
            att_rolls_won = 0
            for j in range(3):
                att_roll = (random.randint(40, 100) / 100) * att_value
                def_roll = (random.randint(40, 100) / 100) * def_value
                if att_roll > def_roll:
                    att_rolls_won += 1
            if att_rolls_won == 3:
                immense += 1
            elif att_rolls_won == 2:
                moderate += 1
            elif att_rolls_won == 1:
                pyrrhic += 1
            else:
                failure += 1
        immense = round(immense/10, 1)
        moderate = round(moderate/10, 1)
        pyrrhic = round(pyrrhic/10, 1)
        failure = round(failure/10, 1)
        description = f"{att_soldiers} soldiers and {att_tanks} tanks vs\n{def_soldiers} soldiers and {def_tanks} tanks"
        embed = discord.Embed(title="Ground Battle Simulator", description=description)
        embed.add_field(name=f"{immense}%", value="Immense Triumph", inline=False)
        embed.add_field(name=f"{moderate}%", value="Moderate Success", inline=False)
        embed.add_field(name=f"{pyrrhic}%", value="Pyrrhic Victory", inline=False)
        embed.add_field(name=f"{failure}%", value="Utter Failure", inline=False)
        await ctx.send(embed=embed)




def setup(bot):
    bot.add_cog(Calculations(bot))