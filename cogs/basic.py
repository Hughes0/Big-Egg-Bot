import discord
from discord.ext import commands
import requests
import json
import sys
sys.path.append('..')
import helpers




class Basic(commands.Cog):

    def __init__(self, bot):
        self.bot = bot    


    @commands.command()
    async def project(self, ctx, name):
        if not name:
            raise ValueError("Missing name")
        query = f"""
            SELECT * FROM projects WHERE name = '{name}';
        """
        results = helpers.read_query('databases/game_data.sqlite', query)
        project_data = results[0]
        embed = discord.Embed(title=project_data[0], description=project_data[1])
        embed.set_thumbnail(url=project_data[2])
        cost = json.loads(project_data[3])
        for resource in cost:
            embed.add_field(name='{:,}'.format(int(cost[resource])), value=resource.capitalize())
        await ctx.send(embed=embed)

    @project.error
    async def project_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}project <name>`")


def setup(bot):
    bot.add_cog(Basic(bot))