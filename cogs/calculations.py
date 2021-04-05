import discord
from discord.ext import commands
import math
import random
import requests
import sys
sys.path.append('..')
import helpers


def battle_odds(att_value, def_value):
    immense, moderate, pyrrhic, failure = (0, 0, 0, 0)
    # simulate 1000 battles and save their results
    for i in range(1000):
        att_rolls_won = 0
        # simulate 3 rolls
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
    if immense > 50:
        color = 0x0fb500 # green
    elif failure > 50:
        color = 0xff1100 # red
    else: 
        color = 0xf0d800 # yellow
    return immense, moderate, pyrrhic, failure, color



class Calculations(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot


    @commands.command(brief="War ranges")
    async def range(self, ctx, score):
        # level 1 command
        if not check(ctx, 1):
            raise Exception("Missing permissions")
            return
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
        # level 1 command
        if not check(ctx, 1):
            raise Exception("Missing permissions")
            return
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
        immense, moderate, pyrrhic, failure, color = battle_odds(att_value, def_value)
        description = f"{att_soldiers} soldiers and {att_tanks} tanks vs\n{def_soldiers} soldiers and {def_tanks} tanks"
        embed = discord.Embed(title="Ground Battle Simulator", description=description, color=color)
        embed.add_field(name=f"{immense}%", value="Immense Triumph", inline=False)
        embed.add_field(name=f"{moderate}%", value="Moderate Success", inline=False)
        embed.add_field(name=f"{pyrrhic}%", value="Pyrrhic Victory", inline=False)
        embed.add_field(name=f"{failure}%", value="Utter Failure", inline=False)
        await ctx.send(embed=embed)

    @ground.error
    async def ground_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}ground <att soldiers> <att tanks> <def soldiers> <def tanks>`")


    @commands.command(brief="Airstrike simulator")
    async def air(self, ctx, att_planes, def_planes):
        # level 1 command
        if not check(ctx, 1):
            raise Exception("Missing permissions")
            return
        try:
            att_planes = int(att_planes.replace(',', ''))
            def_planes = int(def_planes.replace(',', ''))
        except:
            raise ValueError("Invalid input")
        if att_planes > 10000 or def_planes > 10000:
            raise ValueError("Values too large")
        att_value = att_planes * 3
        def_value = def_planes * 3
        immense, moderate, pyrrhic, failure, color = battle_odds(att_value, def_value)
        description = f"{att_planes} planes vs\n{def_planes} planes"
        embed = discord.Embed(title="Airstrike Simulator", description=description, color=color)
        embed.add_field(name=f"{immense}%", value="Immense Triumph", inline=False)
        embed.add_field(name=f"{moderate}%", value="Moderate Success", inline=False)
        embed.add_field(name=f"{pyrrhic}%", value="Pyrrhic Victory", inline=False)
        embed.add_field(name=f"{failure}%", value="Utter Failure", inline=False)
        await ctx.send(embed=embed)

    @air.error
    async def air_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}air <att planes> <def planes>`")


    @commands.command(brief="Naval battle simulator")
    async def naval(self, ctx, att_ships, def_ships):
        # level 1 command
        if not check(ctx, 1):
            raise Exception("Missing permissions")
            return
        try:
            att_ships = int(att_ships.replace(',', ''))
            def_ships = int(def_ships.replace(',', ''))
        except:
            raise ValueError("Invalid input")
        if att_ships > 1000 or def_ships > 1000:
            raise ValueError("Values too large")
        att_value = att_ships * 3
        def_value = def_ships * 3
        immense, moderate, pyrrhic, failure, color = battle_odds(att_value, def_value)
        description = f"{att_ships} ships vs\n{def_ships} ships"
        embed = discord.Embed(title="Naval Battle Simulator", description=description, color=color)
        embed.add_field(name=f"{immense}%", value="Immense Triumph", inline=False)
        embed.add_field(name=f"{moderate}%", value="Moderate Success", inline=False)
        embed.add_field(name=f"{pyrrhic}%", value="Pyrrhic Victory", inline=False)
        embed.add_field(name=f"{failure}%", value="Utter Failure", inline=False)
        await ctx.send(embed=embed)

    @naval.error
    async def naval_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}naval <att ships> <def ships>`")


    @commands.command(brief="City costs calculator")
    async def citycosts(self, ctx, start_city, goal_city, project, percent_discount):
        # level 1 command
        if not check(ctx, 1):
            raise Exception("Missing permissions")
            return
        # check if inputs are valid
        try:
            start_city = int(start_city)
            goal_city = int(goal_city)
            percent_discount = int(percent_discount) / 100
            project = project.lower()
            if project not in ['0', 'cp', 'acp']:
                raise ValueError("Error selecting project")
        except:
            raise ValueError("Error parsing inputs")
        cost = 0
        # iterate through cities to purchase
        for current_city in range(start_city, goal_city):
            # calculate cost of next city
            next_city_cost = 50000*((current_city)-1)**3 + 150000*(current_city) + 75000
            # apply city planning discount when next city is at least 12
            if project == 'cp' and current_city >= 11:
                next_city_cost -= 50000000
            elif project == 'acp':
                # apply full advanced city planning discount when next city is at least 16
                if current_city >= 16:
                    next_city_cost -= 150000000
                # apply partial advanced city planning discount when next city is at least 11 but less than 16
                elif current_city >= 11:
                    next_city_cost -= 50000000
            # apply discounts to cost of next city
            next_city_cost -= (next_city_cost * percent_discount)
            cost += next_city_cost
        cost = round(cost, 2)
        embed = discord.Embed(title=f"${'{:,}'.format(cost)}", description=f"c{start_city} - c{goal_city}")
        embed.add_field(name="Project Discount", value=f"${'{:,}'.format(absolute_discount)}")
        embed.add_field(name="Percent Discount", value=f"{percent_discount*100}%")
        await ctx.send(embed=embed)

    @citycosts.error
    async def citycosts_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}citycosts <start city> <goal city> <project> <percent discount>`")


    @commands.command()
    async def spies(self, ctx, nation_id):
        # level 2 command
        helpers.check(ctx, 2)
        # check if inputs are valid
        try:
            nation_id = int(nation_id)
        except:
            raise ValueError("Invalid input")
        await ctx.send("Calculating spies...")
        # get nation API data
        nation_info = requests.get(f"http://politicsandwar.com/api/nation/id={nation_id}&key={helpers.apikey()['key']}").json()
        # catch API errors
        helpers.catch_api_error(data=nation_info, version=1)
        war_policy = nation_info['war_policy']
        spies = helpers.spy_calculator(nation_id,war_policy)
        embed = discord.Embed(title=f"Nation `id: {nation_id}` has `{spies}` spies",
                            description=f"[politicsandwar.com/nation/id={nation_id}](https://politicsandwar.com/nation/id={nation_id})")
        embed.set_footer(text=f"War Policy: {war_policy}")
        await ctx.send(embed=embed)

    @spies.error
    async def spies_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}spies <nation_id>`")



def setup(bot):
    bot.add_cog(Calculations(bot))