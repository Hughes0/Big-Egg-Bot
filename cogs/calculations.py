import discord
from discord.ext import commands
import math
import random
import requests
import math
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


def city_income(city_id):
    url = f"https://politicsandwar.com/api/city/id={city_id}&key={helpers.apikey()}"
    city_data = requests.get(url).json()
    if "error" in city_data:
        raise Exception(city_data['error'])
    url = f"https://politicsandwar.com/api/nation/id={city_data['nationid']}&key={helpers.apikey()}"
    nation_data = requests.get(url).json()
    # initialize total income variables
    gross_cash = 0
    upkeep = 0
    food_production = 0
    food_consumption = 0
    net_coal = 0
    net_oil = 0
    net_uranium = 0
    net_lead = 0
    net_iron = 0
    net_bauxite = 0
    net_gasoline = 0
    net_munitions = 0
    net_steel = 0
    net_aluminum = 0
    # gross cash
    commerce = city_data['commerce']
    if int(nation_data['inttradecenter']) == 0:
        commerce = min(100, commerce)
    gross_cash += (((commerce/50) * 0.725) + 0.725) * city_data['population']
    if nation_data['domestic_policy'] == "Open Markets":
        gross_cash *= 1.01
    # upkeep
    upkeep += int(city_data['imp_coalpower']) * 1200
    upkeep += int(city_data['imp_oilpower']) * 1800
    upkeep += int(city_data['imp_nuclearpower']) * 10500
    upkeep += int(city_data['imp_windpower']) * 500
    upkeep += int(city_data['imp_policestation']) * 750
    upkeep += int(city_data['imp_hospital']) * 1000
    upkeep += int(city_data['imp_recyclingcenter']) * 2500
    upkeep += int(city_data['imp_subway']) * 3250
    upkeep += int(city_data['imp_supermarket']) * 600
    upkeep += int(city_data['imp_bank']) * 1800
    upkeep += int(city_data['imp_mall']) * 5400
    upkeep += int(city_data['imp_stadium']) * 12150
    # general rss production function
    def production(current_imps, max_imps, base_prod):
        bonus = 1 + ((0.5 * (current_imps - 1)) / (max_imps - 1))
        return current_imps * base_prod * bonus
    # food
    farms = int(city_data['imp_farm'])
    bonus = 1 + ((0.5 * (farms - 1)) / (20 - 1))
    in_antarctica = nation_data['continent'] == "Antarctica"
    project = nation_data['massirrigation']
    season_mod = 1
    if not in_antarctica:
        season = nation_data['season']
        if season == "Summer":
            season_mod = 1.2
        elif season == "Winter":
            season_mod = 0.8
    if project == "0":
        land_divisor = 500
    elif project == "1":
        land_divisor = 400
    if in_antarctica:
        land_divisor *= 2
    # base food production = (land / land divisor) * farms * bonus * 12 (turns in a day)
    base_prod = (float(city_data['land']) / land_divisor) * farms * bonus * 12
    # real food production
    radiation_penalty = nation_data['radiation_index']/(-1000)
    food_production += max((base_prod * season_mod * (1 + radiation_penalty)) ,0)
    upkeep += 300*farms
    # food consumption
    in_war = nation_data['offensivewars'] == nation_data['defensivewars'] == 0
    if in_war:
        soldier_consumption = 750
    else:
        soldier_consumption = 500
    food_consumption += round(((city_data['population'] / 1000) + \
            ((int(nation_data['soldiers']) / nation_data['cities']) / soldier_consumption)), 1)
    # coal
    coal_mines = int(city_data['imp_coalmine'])
    net_coal += production(coal_mines, 10, 3)
    upkeep += 400 * coal_mines
    # oil
    oil_wells = int(city_data['imp_oilwell'])
    net_oil += production(oil_wells, 10, 3)
    upkeep += 600 * oil_wells
    # uranium
    uranium_mines = int(city_data['imp_uramine'])
    if nation_data['uraniumenrich'] == "1":
        base_prod = 6
    else:
        base_prod = 3
    net_uranium += production(uranium_mines, 5, base_prod)
    # power usage (coal, oil, uranium)
    infrastructure = float(city_data['infrastructure'])
    covered_by_nuclear = min(int(city_data['imp_nuclearpower']) * 2000, infrastructure)
    net_uranium -= round(math.ceil(covered_by_nuclear / 1000) * 1.2, 1)
    not_covered_by_nuclear = infrastructure - covered_by_nuclear
    if not_covered_by_nuclear > 0:
        net_coal -= math.ceil((min(int(city_data['imp_coalpower']) * 500, not_covered_by_nuclear)) / 100) * 1.2
        net_oil -= math.ceil((min(int(city_data['imp_oilpower']) * 500, not_covered_by_nuclear)) / 100) * 1.2
    # lead
    lead_mines = int(city_data['imp_leadmine'])
    net_lead += production(lead_mines, 10, 3)
    upkeep += 1500 * lead_mines
    # iron
    iron_mines = int(city_data['imp_ironmine'])
    net_iron += production(iron_mines, 10, 3)
    upkeep += 1600 * iron_mines
    # bauxite
    bauxite_mines = int(city_data['imp_bauxitemine'])
    net_bauxite += production(bauxite_mines, 10, 3)
    upkeep += 1600 * bauxite_mines
    # gasoline
    oil_refineries = int(city_data['imp_gasrefinery'])
    if nation_data['emgasreserve'] == "1":
        base_prod  = 12
        base_usage = 6
    else:
        base_prod = 6
        base_usage = 3
    net_gasoline += production(oil_refineries, 5, base_prod)
    net_oil -= production(oil_refineries, 5, base_usage)
    upkeep += 4000 * oil_refineries
    # munitions
    munitions_factories = int(city_data['imp_munitionsfactory'])
    if nation_data['armsstockpile'] == "1":
        base_prod  = 24.12
        base_usage = 8.04
    else:
        base_prod = 18
        base_usage = 6
    net_munitions += production(munitions_factories, 5, base_prod)
    net_lead -= production(munitions_factories, 5, base_usage)
    upkeep += 3500 * munitions_factories
    # steel
    steel_mills = int(city_data['imp_steelmill'])
    if nation_data['ironworks'] == "1":
        base_prod  = 12.24
        base_usage = 4.08
    else:
        base_prod = 9
        base_usage = 3
    net_steel += production(steel_mills, 5, base_prod)
    net_coal -= production(steel_mills, 5, base_usage)
    net_iron -= production(steel_mills, 5, base_usage)
    upkeep += 4000 * steel_mills
    # aluminum
    aluminum_refineries = int(city_data['imp_aluminumrefinery'])
    if nation_data['bauxiteworks'] == "1":
        base_prod  = 12.24
        base_usage = 4.08
    else:
        base_prod = 9
        base_usage = 3
    net_aluminum += production(aluminum_refineries, 5, base_prod)
    net_bauxite -= production(aluminum_refineries, 5, base_usage)
    upkeep += 2500 * aluminum_refineries
    return gross_cash, upkeep, food_production, food_consumption, net_coal, net_oil, net_uranium, \
            net_lead, net_iron, net_bauxite, net_gasoline, net_munitions, net_steel, net_aluminum




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


    @commands.command()
    @commands.check(helpers.perms_one)
    async def value(self, ctx, *resources):
        prices = helpers.prices([resources[i+1].lower() for i in range(0, len(resources), 2)])
        total_value = 0
        embed = discord.Embed(title="Value")
        for i in range(0, len(resources), 2):
            amount = float(resources[i].replace(',', ''))
            resource = resources[i+1].lower()
            val = amount * int(prices[resource]['avgprice'])
            total_value += val
            embed.add_field(name=f"{'{:,}'.format(amount)} {resource}", value=f"${'{:,}'.format(val)}")
        embed.title = f"${'{:,}'.format(total_value)}"
        await ctx.send(embed=embed)

    @value.error
    async def value_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}value <amount> <resource> [amount] [resource] ...`")


    @commands.group(pass_context=True)
    @commands.check(helpers.perms_two)
    async def income(self, ctx):
        # case no action selected
        if ctx.invoked_subcommand is None:
            raise Exception("Invalid action")

    @income.command()
    async def city(self, ctx, city_id):
        try:
            city_id = int(city_id)
        except:
            raise Exception("Invalid input")
        gross_cash, upkeep, food_production, food_consumption, net_coal, net_oil, net_uranium, \
            net_lead, net_iron, net_bauxite, net_gasoline, net_munitions, net_steel, net_aluminum = city_income(city_id)
        text = f"""
        Gross Cash: {gross_cash}
        Upkeep: {upkeep}
        Net Cash: {gross_cash - upkeep}
        Food Prod: {food_production}
        Food Use: {food_consumption}
        Coal: {net_coal}
        Oil: {net_oil}
        Uranium: {net_uranium}
        Lead: {net_lead}
        Iron: {net_iron}
        Bauxite: {net_bauxite}
        Gasoline: {net_gasoline}
        Munitions: {net_munitions}
        Steel: {net_steel}
        Aluminum: {net_aluminum}
        """
        await ctx.send(text)
        

    @income.command()
    async def nation(self, ctx, nation_id):
        return

    @income.command()
    async def alliance(self, ctx, alliance_id):
        return

    @income.error
    async def income_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}income <object>`")



def setup(bot):
    bot.add_cog(Calculations(bot))