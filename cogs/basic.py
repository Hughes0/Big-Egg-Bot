import discord
from discord.ext import commands
import datetime
import requests
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))

import helpers




class Basic(commands.Cog):

    def __init__(self, bot):
        self.bot = bot    


    @commands.command()
    @commands.check(helpers.perms_one)
    async def project(self, ctx, name):
        if not name:
            raise ValueError("Missing name")
        query = f"""
            SELECT * FROM projects WHERE name = '{name}';
        """
        results = helpers.read_query(query)
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


    @commands.command()
    @commands.check(helpers.perms_one)
    async def market(self, ctx):
        print("here")
        prices = helpers.prices("all")
        embed = discord.Embed(title="Market Overview", color=ctx.author.color, timestamp=datetime.datetime.now())
        for resource in prices:
            try:
                sell = int(prices[resource]['lowestbuy']['price'])
            except:
                sell = 0
            try:
                buy = int(prices[resource]['highestbuy']['price'])
            except:
                buy = 0
            if sell == 0 or buy == 0:
                margin = 0
            else:
                margin = sell - buy
            embed.add_field(name=resource.capitalize(), \
                    value=f"{sell} sell\n{buy} buy\n{margin} margin")
        await ctx.send(embed=embed)


    @commands.command()
    @commands.check(helpers.perms_one)
    async def war(self, ctx, war_id):
        try:
            war_id = int(war_id)
        except:
            raise Exception("Invalid input")
        apikey = helpers.apikey()
        data = requests.get(f"https://politicsandwar.com/api/war/{war_id}&key={apikey}").json()['war'][0]
        att_id = data["aggressor_id"]
        def_id = data["defender_id"]
        attacker = requests.get(f"http://politicsandwar.com/api/nation/id={att_id}&key={apikey}").json()
        defender = requests.get(f"http://politicsandwar.com/api/nation/id={def_id}&key={apikey}").json()
        embed_title = f"{attacker['leadername']} of {attacker['name']} ({att_id})\n\
                attacked\n{defender['leadername']} of {defender['name']} ({def_id})"
        embed = discord.Embed(title=embed_title, \
                description=f"{data['war_type'].capitalize()} at {data['date']}\nReason: {data['war_reason']}", \
                color=ctx.author.color, url=f"https://politicsandwar.com/nation/war/timeline/war={war_id}")
        categories_field = f"""Alliance
        AA ID
        Cities
        Score
        -
        MAPs
        Res
        GC
        AS
        Blockaded
        Fortified
        -
        Soldiers
        Tanks
        Planes
        Ships"""
        if data['ground_control'] == att_id:
            att_gc = True
            def_gc = False
        elif data['ground_control'] == def_id:
            att_gc = False
            def_gc = True
        else: att_gc = def_gc = False
        if data['air_superiority'] == att_id:
            att_as = True
            def_as = False
        elif data['air_superiority'] == def_id:
            att_as = False
            def_as = True
        else: att_as = def_as = False
        if data['blockade'] == att_id:
            att_blockaded = False
            def_blockaded = True
        elif data['blockade'] == def_id:
            att_blockaded = True
            def_blockaded = False
        else: att_blockaded = def_blockaded = False
        attacker_field = f"""{data['aggressor_alliance_name']}
        {attacker['allianceid']}
        {attacker['cities']}
        {attacker['score']}
        -
        {data['aggressor_military_action_points']}
        {data['aggressor_resistance']}
        {att_gc}
        {att_as}
        {att_blockaded}
        {data['aggressor_is_fortified']}
        -
        {attacker['soldiers']}
        {attacker['tanks']}
        {attacker['aircraft']}
        {attacker['ships']}"""
        embed.add_field(name="-", value=categories_field,inline=True)
        embed.add_field(name="Attacker", value=attacker_field)
        defender_field = f"""{data['defender_alliance_name']}
        {defender['allianceid']}
        {defender['cities']}
        {defender['score']}
        -
        {data['defender_military_action_points']}
        {data['defender_resistance']}
        {def_gc}
        {def_as}
        {def_blockaded}
        {data['defender_is_fortified']}
        -
        {defender['soldiers']}
        {defender['tanks']}
        {defender['aircraft']}
        {defender['ships']}"""
        embed.add_field(name="Defender", value=defender_field)
        embed.set_footer(text=f"Turns left: {data['turns_left']}")
        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Basic(bot))