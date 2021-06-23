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
    @commands.check(helpers.perms_one)
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
    @commands.check(helpers.perms_one)
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
    @commands.check(helpers.perms_one)
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
    @commands.check(helpers.perms_one)
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
    @commands.check(helpers.perms_one)
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


def setup(bot):
    bot.add_cog(Archive(bot))