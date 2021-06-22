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
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}prices_change <argument=value>`")


def setup(bot):
    bot.add_cog(Archive(bot))