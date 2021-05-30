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
    @commands.check(helpers.perms_one)
    async def range(self, ctx, score):
        try:
            score = float(score.replace(',', ''))
            if score > 25000:
                raise ValueError("Invalid input")
        except:
            raise ValueError("Invalid input")
        min_off, max_off = int(round(score*0.75, 0)), int(round(score*1.75, 0))
        min_def, max_def = int(round(score/1.75, 0)), int(round(score/0.75, 0))
        min_spy, max_spy = int(round(score*0.4, 0)), int(round(score*2.5, 0))
        embed = discord.Embed(title=f"{score} ns", description="Score Ranges", color=ctx.author.color)
        embed.add_field(name=f"{min_off} - {max_off}", value="Offensive War Range", inline=False)
        embed.add_field(name=f"{min_def} - {max_def}", value="Defensive War Range", inline=False)
        embed.add_field(name=f"{min_spy} - {max_spy}", value="Spy Range", inline=False)
        await ctx.send(embed=embed)

    @range.error
    async def range_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}range <score>`")
        

    @commands.command(brief="Ground battle simulator")
    @commands.check(helpers.perms_one)
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
        immense, moderate, pyrrhic, failure, color = battle_odds(att_value, def_value)
        description = f"{att_soldiers} soldiers and {att_tanks} tanks vs\n{def_soldiers} soldiers and {def_tanks} tanks"
        embed = discord.Embed(title="Ground Battle Simulator", description=description, color=color)
        embed.add_field(name=f"{immense}%", value="Immense Triumph (10 res)", inline=False)
        embed.add_field(name=f"{moderate}%", value="Moderate Success (7 res)", inline=False)
        embed.add_field(name=f"{pyrrhic}%", value="Pyrrhic Victory (4 res)", inline=False)
        embed.add_field(name=f"{failure}%", value="Utter Failure (0 res)", inline=False)
        await ctx.send(embed=embed)

    @ground.error
    async def ground_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}ground <att soldiers> <att tanks> <def soldiers> <def tanks>`")


    @commands.command(brief="Airstrike simulator")
    @commands.check(helpers.perms_one)
    async def air(self, ctx, att_planes, def_planes):
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
        embed.add_field(name=f"{immense}%", value="Immense Triumph (12 res)", inline=False)
        embed.add_field(name=f"{moderate}%", value="Moderate Success (9 res)", inline=False)
        embed.add_field(name=f"{pyrrhic}%", value="Pyrrhic Victory (6 res)", inline=False)
        embed.add_field(name=f"{failure}%", value="Utter Failure (0 res)", inline=False)
        await ctx.send(embed=embed)

    @air.error
    async def air_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}air <att planes> <def planes>`")


    @commands.command(brief="Naval battle simulator")
    @commands.check(helpers.perms_one)
    async def naval(self, ctx, att_ships, def_ships):
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
        embed.add_field(name=f"{immense}%", value="Immense Triumph (14 res)", inline=False)
        embed.add_field(name=f"{moderate}%", value="Moderate Success (11 res)", inline=False)
        embed.add_field(name=f"{pyrrhic}%", value="Pyrrhic Victory (8 res)", inline=False)
        embed.add_field(name=f"{failure}%", value="Utter Failure (0 res)", inline=False)
        await ctx.send(embed=embed)

    @naval.error
    async def naval_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}naval <att ships> <def ships>`")


    @commands.command(brief="City costs calculator")
    @commands.check(helpers.perms_one)
    async def citycosts(self, ctx, start_city, goal_city, project, percent_discount):
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
        embed = discord.Embed(title=f"${'{:,}'.format(cost)}", \
                description=f"c{start_city} - c{goal_city}", \
                color=ctx.author.color)
        embed.add_field(name=project.upper(), value="Project", inline=False)
        embed.add_field(name=f"{percent_discount*100}%", value="Percent Discount", inline=False)
        await ctx.send(embed=embed)

    @citycosts.error
    async def citycosts_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}citycosts <start city> <goal city> <project> <percent discount>`")


    @commands.command()
    @commands.check(helpers.perms_one)
    async def infracosts(self, ctx, start_infra, goal_infra, cities, percent_discount):
        # check if inputs are valid
        try:
            start_infra = int(start_infra)
            goal_infra = int(goal_infra)
            cities = int(cities)
            percent_discount = int(percent_discount)
        except:
            raise ValueError("Invalid input")
        if (start_infra > goal_infra or start_infra > 10000 or 
            goal_infra > 10000 or start_infra < 0 or goal_infra < 0 or
            cities > 60 or cities < 0 or 
            percent_discount < 0 or percent_discount > 100):
            raise ValueError("Values out of range")
        percent_discount = percent_discount / 100
        total_cost = 0
        # get infra amount to buy
        to_buy = goal_infra - start_infra
        # split amount to buy into chunks of 100 (price changes every 100)
        chunks = math.floor(to_buy / 100)
        # calculate leftover to buy that does not fit into the chunks
        leftover = to_buy - chunks * 100
        # iterate through chunks
        count = 0
        while count < chunks:
            # get the starting infra amount for current chunk
            chunk_starting_infra = start_infra + (count * 100)
            # calculate current of that chunk and add it to total
            cost = 100*((((chunk_starting_infra-10)**2.2) / 710) + 300)
            total_cost += cost
            count += 1
        # calculate cost of leftover to buy and add to total cost
        if leftover > 0:
            cost = leftover*(((((start_infra+(chunks*100))-10)**2.2) / 710) + 300)
            total_cost += cost
        # apply discount and multiply by selected number of cities
        total_cost *= cities
        total_cost -= (total_cost * percent_discount)
        total_cost = round(total_cost, 1)
        # create embed
        embed = discord.Embed(title=f"${'{:,}'.format(total_cost)}", \
                description=f"{start_infra} - {goal_infra} infra", \
                color=ctx.author.color)
        embed.add_field(name=cities, value="Cities", inline=False)
        embed.add_field(name=f"{percent_discount*100}%", value="Percent Discount", inline=False)
        await ctx.send(embed=embed)



    @commands.command()
    @commands.check(helpers.perms_two)
    async def spies(self, ctx, nation_id):
        # check if inputs are valid
        try:
            nation_id = int(nation_id)
        except:
            raise ValueError("Invalid input")
        await ctx.send("Calculating spies...")
        # get nation API data
        nation_info = requests.get(f"http://politicsandwar.com/api/nation/id={nation_id}&key={helpers.apikey()}").json()
        # catch API errors
        helpers.catch_api_error(data=nation_info, version=1)
        war_policy = nation_info['war_policy']
        spies = helpers.spies(nation_id, war_policy)
        embed = discord.Embed(title=f"Nation `id: {nation_id}` has `{spies}` spies",
                            description=f"[politicsandwar.com/nation/id={nation_id}](https://politicsandwar.com/nation/id={nation_id})", \
                            color=ctx.author.color)
        embed.set_footer(text=f"War Policy: {war_policy}")
        await ctx.send(embed=embed)

    @spies.error
    async def spies_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot_command_prefix}spies <nation_id>`")


    @commands.command()
    @commands.check(helpers.perms_ten)
    async def warchest(self, ctx, cities):
        # check if input is valid
        try:
            cities = int(cities)
        except:
            raise ValueError("Invalid input")
        if cities > 60 or cities < 1:
            raise ValueError("Inputs out of range")
        data = helpers.get_data()
        # get alliance id from server id
        data['discord_to_alliance'][str(ctx.guild.id)]
        # get wc reqs based on alliance
        # return in embed
        await ctx.send("Command incomplete")
        
        
    @warchest.error
    async def warchest_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}warchest <cities>`")



def setup(bot):
    bot.add_cog(Calculations(bot))