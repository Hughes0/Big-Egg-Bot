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
    async def treaties(self, ctx, *args):
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
            embed = discord.Embed(title=f"{len(treaties)} Treaties", description=f"{detected_args}")
            for treaty in sublist:
                embed.add_field(name=f"{id_to_name[str(treaty['source'])]} to {id_to_name[str(treaty['target'])]}", value=f"{treaty['type']} on {treaty['entry_date']}")
            embed.set_footer(text=f"Page: {page}")
            page += 1
            await ctx.send(embed=embed)

    @treaties.error
    async def treaties_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}treaties`")


def setup(bot):
    bot.add_cog(Archive(bot))