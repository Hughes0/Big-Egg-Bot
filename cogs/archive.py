import discord
from discord.ext import commands
import datetime
import requests
import os
import json
import sys
sys.path.append('..')
import helpers




class Archive(commands.Cog):

    def __init__(self, bot):
        self.bot = bot    

    @commands.command()
    @commands.check(helpers.perms_six)
    async def treaties_overview(self, ctx, *args):
        args = helpers.parse_keyword_args(args)
        archive_api_url = os.getenv('API_URL')
        parameters = '&'.join([f"{arg}={args[arg]}" for arg in args])
        url = f'{archive_api_url}/api/treaties?{parameters}'
        data = requests.get(url).json()
        args = data['request_data']['arguments']
        detected_args = {
            arg: args[arg] for arg in args if args[arg] is not None
        }
        treaties = data['treaties']
        id_to_name = helpers.alliance_id_to_name()
        page = 1
        for sublist in helpers.paginate_list(treaties, 15):
            embed = discord.Embed(title=f"{len(treaties)} Treaties | Overview", description=f"{detected_args}")
            for treaty in sublist:
                embed.add_field(name=f"{id_to_name[str(treaty['source'])]} to {id_to_name[str(treaty['target'])]}", value=f"{treaty['type']} on {treaty['entry_date']}")
            embed.set_footer(text=f"Page: {page}")
            page += 1
            await ctx.send(embed=embed)


    @treaties_overview.error
    async def treaties_overview_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}treaties_overview <argument=value>`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def treaties_change(self, ctx, start_date, end_date, alliance_ids=None):
        archive_api_url = os.getenv('API_URL')
        id_to_name = helpers.alliance_id_to_name()
        if alliance_ids:
            alliance_ids = alliance_ids.split(',')
            parameters = '&'.join([f'alliance_id={id}' for id in alliance_ids])
            alliances = f"{', '.join([id_to_name[str(id)] for id in alliance_ids])}"
        else:
            parameters = ""
            alliances = "All Alliances"
        url = f'{archive_api_url}/api/treaties?{parameters}&entry_date={start_date}'
        data = requests.get(url).json()
        start_treaties = helpers.remove_dates(data['treaties'], 'entry_date')
        url = f'{archive_api_url}/api/treaties?{parameters}&entry_date={end_date}'
        data = requests.get(url).json()
        end_treaties = helpers.remove_dates(data['treaties'], 'entry_date')
        added = [treaty for treaty in end_treaties if treaty not in start_treaties]
        removed = [treaty for treaty in start_treaties if treaty not in end_treaties]
        page = 1
        for sublist in helpers.paginate_list(added, 15):
            embed = discord.Embed(title=f"{len(added)} Treaties Added | Change", \
                    description=alliances)
            for treaty in sublist:
                embed.add_field(name=f"{id_to_name[str(treaty['source'])]} to {id_to_name[str(treaty['target'])]}", value=f"{treaty['type']}")
            embed.set_footer(text=f"Page: {page}")
            page += 1
            await ctx.send(embed=embed)
        if not added:
            await ctx.send("No treaties added")
        page = 1
        for sublist in helpers.paginate_list(removed, 15):
            embed = discord.Embed(title=f"{len(removed)} Treaties Removed | Change", \
                    description=alliances)
            for treaty in sublist:
                embed.add_field(name=f"{id_to_name[str(treaty['source'])]} to {id_to_name[str(treaty['target'])]}", value=f"{treaty['type']}")
            embed.set_footer(text=f"Page: {page}")
            page += 1
            await ctx.send(embed=embed)
        if not removed:
            await ctx.send("No treaties removed")


    @treaties_change.error
    async def treaties_change_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}treaties_change <argument=value>`")

    
    @commands.command()
    @commands.check(helpers.perms_six)
    async def prices_overview(self, ctx, *args):
        args = helpers.parse_keyword_args(args)
        archive_api_url = os.getenv('API_URL')
        parameters = '&'.join([f"{arg}={args[arg]}" for arg in args])
        url = f'{archive_api_url}/api/prices?{parameters}'
        data = requests.get(url).json()
        args = data['request_data']['arguments']
        detected_args = {
            arg: args[arg] for arg in args if args[arg] is not None
        }
        prices = data['prices']
        page = 1
        for sublist in helpers.paginate_list(prices, 15):
            embed = discord.Embed(title=f"{len(prices)} Price Entries | Oveview", description=f"{detected_args}")
            for treaty in sublist:
                embed.add_field(name=f"{treaty['resource']} on {treaty['entry_date']} {':'.join(treaty['entry_time'].split(':')[:2])}", \
                        value=f"Avg: {treaty['avg_price']}\nSell: {treaty['sell_market']}\nBuy: {treaty['buy_market']}")
            embed.set_footer(text=f"Page {page}")
            page += 1
            await ctx.send(embed=embed)

    @prices_overview.error
    async def prices_overview_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}prices_overview <argument=value>`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def prices_change(self, ctx, start_date, end_date):
        archive_api_url = os.getenv('API_URL')
        url = f'{archive_api_url}/api/prices?entry_date={start_date}'
        data = requests.get(url).json()
        start_prices = helpers.remove_dates(data['prices'], 'entry_date')
        url = f'{archive_api_url}/api/prices?entry_date={end_date}'
        data = requests.get(url).json()
        end_prices = helpers.remove_dates(data['prices'], 'entry_date')
        def format(prices, key):
            formatted_dict = {}
            for entry in prices:
                formatted_dict[entry['resource']] = entry[key]
            return formatted_dict
        start_avg = format(start_prices, 'avg_price')
        start_sell = format(start_prices, 'sell_market')
        start_buy = format(start_prices, 'buy_market')
        end_avg = format(end_prices, 'avg_price')
        end_sell = format(end_prices, 'sell_market')
        end_buy = format(end_prices, 'buy_market')
        def price_diff(start_prices, end_prices, resource):
            start_price = start_prices[resource]
            end_price = end_prices[resource]
            return end_price - start_price
        embed = discord.Embed(title="Prices | Change", description=f"{start_date} to {end_date}")
        resources = ['food', 'coal', 'oil', 'uranium', 'lead', 'iron', 'bauxite', 'gasoline', 'munitions', 'steel', 'aluminum']
        for resource in resources:
            embed.add_field(name=resource.capitalize(), value=f"Avg: {price_diff(start_avg, end_avg, resource)}\nSell: {price_diff(start_sell, end_sell, resource)}\nBuy: {price_diff(start_buy, end_buy, resource)}")
        await ctx.send(embed=embed)


    @prices_change.error
    async def prices_change_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}prices_change <start_date> <end_date>`")


    @commands.command(description="use: <nation | alliance>\np1/p2=<id>\np1_type/p2_type=<nation | alliance>\nmin_date/max_date=<yyyy-mm-dd/hh:mm:ss>")
    @commands.check(helpers.perms_six)
    async def stats(self, ctx, use, *args):
        args = helpers.parse_keyword_args(args)
        party_1 = args.get('p1')
        party_1_type = args.get('p1_type')
        party_2 = args.get('p2')
        party_2_type = args.get('p2_type')
        min_date = args.get('min_date')
        max_date = args.get('max_date')
        if not party_1 or not party_1_type:
            raise Exception("p1 and p1_type are required arguments")
        use = use.lower()
        party_1 = party_1.split(",")
        party_1_type = party_1_type.lower()
        archive_api_url = os.getenv('API_URL')
        parameters = '&'.join([f"party_1={entity}" for entity in party_1])
        url = f"{archive_api_url}/api/stats/attacks?{parameters}&party_1_type={party_1_type}"
        args = f"Party 1 {party_1_type}s: {', '.join(party_1)}"
        if party_2 and party_2.lower() != "none":
            party_2 = party_2.split(",")
            party_2_type = party_2_type.lower()
            parameters = '&'.join([f"party_2={entity}" for entity in party_2])
            url += f"&{parameters}&party_2_type={party_2_type}"
            args += f"\nParty 2 {party_2_type}s: {', '.join(party_2)}"
        if min_date:
            url += f"&min_date={min_date}"
            args += f"\nMin date: {min_date.replace('/', ' ')}"
        if max_date:
            url += f"&max_date={max_date}"
            args += f"\nMax date: {max_date.replace('/', ' ')}"
        data = requests.get(url).json()
        party_1_stats = data['party_1']
        party_2_stats = data['party_2']
        categories = [key for key in party_1_stats]
        embed = discord.Embed(title=f"Stats | By {use.capitalize()}", description=args)
        commas = lambda n: "{:,}".format(n)
        for category in categories:
            d = '$' if 'value' in category else ''
            embed.add_field(name=category, value=f"P1 All: {d}{commas(party_1_stats[category])}\n\
                    P2 All: {d}{commas(party_2_stats[category])}\n\
                        P1 Net: {d}{commas(party_1_stats[category]-party_2_stats[category])}")
        await ctx.send(embed=embed)
        
    @stats.error
    async def stats_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}stats <use> <argument=value>`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def alliances_entry(self, ctx, identifier, entry_date):
        archive_api_url = os.getenv('API_URL')
        url = f"{archive_api_url}/api/alliances"
        try:
            identifier = int(identifier)
            identifier_type = 'id'
        except:
            identifier_type = 'name'
        if identifier_type == "name":
            url += f"?name={identifier}"
        elif identifier_type == "id":
            url += f"?id={identifier}"
        url += f"&entry_date={entry_date}"
        data = requests.get(url).json()
        try:
            alliance = data['alliances'][0]
        except:
            raise Exception("No entry found")
        soldiers = alliance['soldiers']
        tanks = alliance['tanks']
        planes = alliance['planes']
        ships = alliance['ships']
        cities = alliance['cities']
        max_soldiers = cities * 15000
        max_tanks = cities * 1250
        max_planes = cities * 75
        max_ships = cities * 15
        barracks = alliance['barracks']
        factories = alliance['factories']
        hangars = alliance['hangars']
        drydocks = alliance['drydocks']
        embed = discord.Embed(title=f"{alliance['name']} ({alliance['id']})", description=alliance['entry_date'])
        c = helpers.commas
        embed.add_field(name="Basic", value=f"Score: {c(alliance['score'])}\nMembers: {alliance['members']}\n \
                    Missiles: {alliance['missiles']}\nNukes: {alliance['nukes']}\nCities: {alliance['cities']}")
        embed.add_field(name="Avg Improvements", \
                value=f"Barracks: {round(barracks/cities,2)}\n \
                    Factories: {round(factories/cities,2)}\n \
                        Hangars: {round(hangars/cities,2)}\n \
                            Drydocks: {round(drydocks/cities,2)}", \
                inline=False)
        embed.add_field(name="Military (current / max)", \
            value=f"Soldiers: {c(soldiers)} / {c(max_soldiers)}\n \
                Tanks: {c(tanks)} / {c(max_tanks)}\n \
                    Planes: {c(planes)} / {c(max_planes)}\n \
                        Ships: {c(ships)} / {c(max_ships)}", \
            inline=False)
        embed.add_field(name="Military (%)", \
            value=f"Soldiers: {round(soldiers/max_soldiers*100)}%\n \
                Tanks: {round(tanks/max_tanks*100)}%\n \
                    Planes: {round(planes/max_planes*100)}%\n \
                        Ships: {round(ships/max_ships*100)}%", \
            inline=False)
        await ctx.send(embed=embed)

    @alliances_entry.error
    async def alliances_entry_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}alliances_entry <identifier> <entry_date:yyyy-mm-dd>`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def alliances_change(self, ctx, identifier, start_date, end_date):
        archive_api_url = os.getenv('API_URL')
        url = f"{archive_api_url}/api/alliances"
        try:
            identifier = int(identifier)
            identifier_type = 'id'
        except:
            identifier_type = 'name'
        if identifier_type == "name":
            url += f"?name={identifier}"
        elif identifier_type == "id":
            url += f"?id={identifier}"
        start_url = url + f"&entry_date={start_date}"
        start_data = requests.get(start_url).json()
        end_url = url + f"&entry_date={end_date}"
        end_data = requests.get(end_url).json()
        try:
            start_entry = start_data['alliances'][0]
            end_entry = end_data['alliances'][0]
        except:
            raise Exception("No entry found for one of the selected dates")
        s_cities = start_entry['cities']
        e_cities = end_entry['cities']
        s_score = start_entry['score']
        e_score = end_entry['score']
        s_members = start_entry['members']
        e_members = end_entry['members']
        s_missiles = start_entry['missiles']
        e_missiles = end_entry['missiles']
        s_nukes = start_entry['nukes']
        e_nukes = end_entry['nukes']
        s_barracks = round(start_entry['barracks'] / s_cities, 2)
        e_barracks = round(end_entry['barracks'] / e_cities, 2)
        s_factories = round(start_entry['factories'] / s_cities, 2)
        e_factories = round(end_entry['factories'] / e_cities, 2)
        s_hangars = round(start_entry['hangars'] / s_cities, 2)
        e_hangars = round(end_entry['hangars'] / e_cities, 2)
        s_drydocks = round(start_entry['drydocks'] / s_cities, 2)
        e_drydocks = round(end_entry['drydocks'] / e_cities, 2)
        s_soldiers = start_entry['soldiers']
        s_soldiers_max = s_cities * 15000
        e_soldiers = end_entry['soldiers']
        e_soldiers_max = e_cities * 15000
        s_tanks = start_entry['tanks']
        s_tanks_max = s_cities * 1250
        e_tanks = end_entry['tanks']
        e_tanks_max = e_cities * 1250
        s_planes = start_entry['planes']
        s_planes_max = s_cities * 75
        e_planes = end_entry['planes']
        e_planes_max = e_cities * 75
        s_ships = start_entry['ships']
        s_ships_max = s_cities * 15
        e_ships = end_entry['ships']
        e_ships_max = e_cities * 15
        s_soldiers_percent = round(s_soldiers/s_soldiers_max*100)
        e_soldiers_percent = round(e_soldiers/e_soldiers_max*100)
        s_tanks_percent = round(s_tanks/s_tanks_max*100)
        e_tanks_percent = round(e_tanks/e_tanks_max*100)
        s_planes_percent = round(s_planes/s_planes_max*100)
        e_planes_percent = round(e_planes/e_planes_max*100)
        s_ships_percent = round(s_ships/s_ships_max*100)
        e_ships_percent = round(e_ships/e_ships_max*100)
        embed = discord.Embed(title=f"{end_entry['name']} ({end_entry['id']})", description=f"{start_entry['entry_date']} -> {end_entry['entry_date']}")
        c = helpers.commas
        embed.add_field(name="Basic", value=f"Score: {c(s_score)} -> {c(e_score)} **({c(round(e_score-s_score, 2))})**\n\
                Members: {s_members} -> {e_members} **({e_members - s_members})**\n\
                    Missiles: {s_missiles} -> {e_missiles} **({e_missiles - s_missiles})**\n\
                        Nukes: {s_nukes} -> {e_nukes} **({e_nukes - s_nukes})**\n\
                            Cities: {s_cities} -> {e_cities} **({e_cities - s_cities})**", inline=False)
        embed.add_field(name="Avg Improvements", value=f"Barracks: {s_barracks} -> {e_barracks} **({round(e_barracks-s_barracks, 2)})**\n\
                Factories: {s_factories} -> {e_factories} **({round(e_factories-s_factories, 2)})**\n\
                    Hangars: {s_hangars} -> {e_hangars} **({round(e_hangars-s_hangars, 2)})**\n\
                        Drydocks: {s_drydocks} -> {e_drydocks} **({round(e_drydocks-s_drydocks, 2)})**", inline=False)
        embed.add_field(name="Military (raw)", value=f"Soldiers: {c(s_soldiers)} -> {c(e_soldiers)} **({c(e_soldiers - s_soldiers)})**\n\
                Tanks: {c(s_tanks)} -> {c(e_tanks)} **({c(e_tanks - s_tanks)})**\n\
                    Planes: {c(s_planes)} -> {c(e_planes)} **({c(e_planes - s_planes)})**\n\
                        Ships: {c(s_ships)} -> {c(e_ships)} **({c(e_ships - s_ships)})**\n", inline=False)
        embed.add_field(name="Military (%)", value=f"Soldiers: {s_soldiers_percent} -> {e_soldiers_percent} **({e_soldiers_percent-s_soldiers_percent}%)**\n\
                Tanks: {s_tanks_percent} -> {e_tanks_percent} **({e_tanks_percent-s_tanks_percent}%)**\n\
                    Planes: {s_planes_percent} -> {e_planes_percent} **({e_planes_percent-s_planes_percent}%)**\n\
                        Ships: {s_ships_percent} -> {e_ships_percent} **({e_ships_percent-s_ships_percent}%)**\n", inline=False)
        await ctx.send(embed=embed)

    @alliances_change.error
    async def alliances_change_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}alliances_change <identifier> <start_date:yyyy-mm-dd> <end_date:yyyy-mm-dd>`")


def setup(bot):
    bot.add_cog(Archive(bot))