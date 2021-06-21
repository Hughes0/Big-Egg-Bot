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


    @commands.group()
    @commands.check(helpers.perms_one)
    async def treaties(self, ctx):
        # case no action selected
        if ctx.invoked_subcommand is None:
            raise Exception("Invalid action")


    @treaties.command()
    async def overview(self, ctx, *args):
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

    @treaties.command()
    async def change(self, ctx, alliance_id, start_date, end_date):
        alliance_ids = alliance_id.split(',')
        archive_api_url = os.getenv('API_URL')
        def remove_dates(treaties):
            new_treaties = []
            for treaty in treaties:
                new_treaty = {
                    'source': treaty['source'],
                    'target': treaty['target'],
                    'type': treaty['type']
                }
                new_treaties.append(new_treaty)
            return new_treaties
        parameters = '&'.join([f'alliance_id={id}' for id in alliance_ids])
        url = f'{archive_api_url}/api/treaties?{parameters}&entry_date={start_date}'
        data = requests.get(url).json()
        start_treaties = remove_dates(data['treaties'])
        url = f'{archive_api_url}/api/treaties?{parameters}&entry_date={end_date}'
        data = requests.get(url).json()
        end_treaties = remove_dates(data['treaties'])
        added = [treaty for treaty in end_treaties if treaty not in start_treaties]
        removed = [treaty for treaty in start_treaties if treaty not in end_treaties]
        id_to_name = helpers.alliance_id_to_name()
        page = 1
        for sublist in helpers.paginate_list(added, 15):
            embed = discord.Embed(title=f"{len(added)} Treaties Added | Change", \
                    description=f"{', '.join([id_to_name[str(id)] for id in alliance_ids])}")
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
                    description=f"{', '.join([id_to_name[str(id)] for id in alliance_ids])}")
            for treaty in sublist:
                embed.add_field(name=f"{id_to_name[str(treaty['source'])]} to {id_to_name[str(treaty['target'])]}", value=f"{treaty['type']}")
            embed.set_footer(text=f"Page: {page}")
            page += 1
            await ctx.send(embed=embed)
        if not removed:
            await ctx.send("No treaties removed")


    @treaties.error
    async def treaties_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}treaties <action> <argument=value>`")


    @commands.group()
    @commands.check(helpers.perms_one)
    async def prices(self, ctx):
        # case no action selected
        if ctx.invoked_subcommand is None:
            raise Exception("Invalid action")

    
    @prices.command()
    async def overview(self, ctx, *args):
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
            embed = discord.Embed(title=f"{len(prices)} Price Entries", description=f"{detected_args}")
            for treaty in sublist:
                embed.add_field(name=f"{treaty['resource']} on {treaty['entry_date']} {':'.join(treaty['entry_time'].split(':')[:2])}", \
                        value=f"Avg: {treaty['avg_price']}\nSell: {treaty['sell_market']}\nBuy: {treaty['buy_market']}")
            embed.set_footer(text=f"Page {page}")
            page += 1
            await ctx.send(embed=embed)

    @prices.error
    async def prices_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}prices <action> <argument=value>`")


def setup(bot):
    bot.add_cog(Archive(bot))