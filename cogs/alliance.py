import discord
from discord.ext import commands
import requests
import datetime
import random
import sys
sys.path.append("..")
import helpers



class Alliance(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    
    @commands.command()
    async def militarization(self, ctx, alliance_id, min_cities=0, max_cities=100):
        # check if inputs are valid
        helpers.check_city_inputs(min_cities, max_cities)
        # get alliance militarization
        # option for overview?

    @militarization.error
    async def militarization_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}militarization <alliance_id> [min_cities] [max_cities]`")


    @commands.command()
    async def aaspies(self, ctx, min_cities=0, max_cities=100):
        # check if inputs are valid
        helpers.check_city_inputs(min_cities, max_cities)
        # get alliance id from server id from keys.json
        data = helpers.get_data()
        alliance_id = data["discord_to_alliance"][str(ctx.guild.id)]
        # get alliance-members API data
        apikey = helpers.apikey(alliance_id=alliance_id, bank_access=True)
        url = f"https://politicsandwar.com/api/alliance-members/?allianceid={alliance_id}&key={apikey}"
        data = requests.get(url).json()
        # catch API errors
        helpers.catch_api_error(data=data, version=1)
        nations = data['nations']
        nations = [nation for nation in nations if nation['cities'] >= min_cities and nation['cities'] <= max_cities]
        by_cities = lambda nation: nation['cities']
        nations.sort(key=by_cities, reverse=True)
        # break nations array into embeds with max 20 nations each
        page = 1
        for i in range(0, len(nations), 20):
            embed = discord.Embed(title=f"Alliance Spies for {nations[0]['alliance']}", description=f"c{min_cities} - c{max_cities}")
            for j in range(20):
                if i+j >= len(nations):
                    break
                nation = nations[i+j]
                if nation['intagncy'] == "1":
                    max_spies = 60
                else:
                    max_spies = 50
                embed.add_field(name=f"{nation['nation']} c{nation['cities']}", value=f"{nation['spies']} / {max_spies}")
            embed.set_footer(text=f"Page {page}")
            await ctx.send(embed=embed)
            page += 1

    @aaspies.error
    async def aaspies_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}aaspies <min_cities> <max_cities>`")


    @commands.command()
    async def activity(self, ctx, alliance_id):
        alliance_id = int(alliance_id)
        url = f"https://politicsandwar.com/api/nations/?alliance_id={alliance_id}&key={helpers.apikey()}"
        response = requests.get(url).json()
        nations = response['nations']
        if not nations or alliance_id == 0:
            raise ValueError("No nations found")
        # catch API errors
        helpers.catch_api_error(data=response, version=1)
        activity = [nation['minutessinceactive'] for nation in nations if nation['vacmode'] == 0 and nation['allianceposition'] > 1]
        notable_times = [ # inclusive
            (0, 0, "currently online"),
            (1, 60, "last hour"),
            (61, 360, "last 12 hours"),
            (361, 1440, "last day"),
            (1441, 4320, "last 3 days")
        ]
        embed = discord.Embed(title=f"Activity Distribution of {nations[0]['alliance']}", description=f"{len(activity)} total members")
        for (minimum, maximum, label) in notable_times:
            raw = len([n for n in activity if maximum >= n >= minimum])
            percent = int(round(100*(raw/len(activity)), 0))
            embed.add_field(name=f"{raw} ({percent}%)", value=label.capitalize(), inline=False)
        await ctx.send(embed=embed)

    @activity.error
    async def activity_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}activity <alliance id>`")


    @commands.command()
    async def counters(self, ctx, att_nation_id, def_alliance_id=None):
        # level 6 command
        helpers.check(ctx, 6)
        if not def_alliance_id:
            # get alliance id from server id from keys.json
            data = helpers.get_data()
            def_alliance_id = data["discord_to_alliance"][str(ctx.guild.id)]
            await ctx.send(f"Defaulting to def_alliance_id of `{def_alliance_id}`")
        try:
            att_nation_id = int(att_nation_id)
            def_alliance_id = int(def_alliance_id)
        except:
            raise ValueError("Invalid input")
        await ctx.send("Calculating counters...")
        # get nation data
        nation = requests.get(f"https://politicsandwar.com/api/nation/id={att_nation_id}/&key={helpers.apikey()}").json()
        helpers.catch_api_error(data=nation, version=1)
        score = float(nation['score'])
        min_def = score / 1.75
        max_def = score / 0.75
        # get alliance members who are in range
        url = f"https://politicsandwar.com/api/v2/nations/{helpers.apikey()}/&alliance_id={def_alliance_id}&alliance_position=2,3,4,5&v_mode=false"
        alliance_response = requests.get(url).json()
        helpers.catch_api_error(data=alliance_response, version=2)
        members = [member for member in alliance_response['data'] if 
                        member['score'] >= min_def and 
                        member['score'] <= max_def
                        and (datetime.datetime.now() - datetime.datetime.strptime(member['last_active'], "%Y-%m-%d %H:%M:%S")).days == 0]
        # sorting order soldiers -> cities -> tanks -> air
        # (order of importance is ascending)
        await ctx.send(f"`{len(members)}`` eligible nations found, sorting...")
        most_soldiers = lambda nation: nation['soldiers']
        members.sort(key=most_soldiers, reverse=True)
        most_cities = lambda nation: nation['cities']
        members.sort(key=most_cities, reverse=True)
        most_tanks = lambda nation: nation['tanks']
        members.sort(key=most_tanks, reverse=True)
        most_air = lambda nation: nation['aircraft']
        members.sort(key=most_air, reverse=True)
        await ctx.send("Returning top 3 nations...")
        for i in range(3):
            nation = members[i]
            embed = discord.Embed(title=nation['nation'])
            await ctx.send(embed=embed)
        
    @counters.error
    async def counters_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}counters <att_nation_id> <def_alliance_id>`")


def setup(bot):
    bot.add_cog(Alliance(bot))