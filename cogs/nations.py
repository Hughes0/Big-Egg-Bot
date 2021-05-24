import discord
from discord.ext import commands
import requests
import json
import sys
sys.path.append('..')
import helpers




class Nations(commands.Cog):

    def __init__(self, bot):
        self.bot = bot    


    @commands.command()
    @commands.check(helpers.perms_six)
    async def timezone(self, ctx, nation_id):
        try:
            nation_id = int(nation_id)
        except:
            raise ValueError("Invalid nation id")
        # get alliance id from server id from keys.json
        data = helpers.get_data()
        alliance_id = data["discord_to_alliance"][str(ctx.guild.id)]
        # get alliance-members API data
        apikey = helpers.apikey(alliance_id=alliance_id, bank_access=True)
        url = f"https://politicsandwar.com/api/alliance-members/?allianceid={alliance_id}&key={apikey}"
        data = requests.get(url).json()
        # catch API errors
        helpers.catch_api_error(data=data, version=1)
        nation = [nation for nation in data['nations'] if nation['nationid'] == nation_id][0]
        if not nation:
            raise Exception(f"No nation by that id found in the alliance {alliance_id}")
        await ctx.send("UTC%+d" % nation['update_tz'])        

    @timezone.error
    async def timezone_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}timezone <nation_id>`")

    
    @commands.command()
    @commands.check(helpers.perms_six)
    async def policies(self, ctx, alliance_id, min_cities=0, max_cities=100):
        try:
            alliance_id = int(alliance_id)
        except:
            raise Exception("Invalid alliance id")
        url = f"https://politicsandwar.com/api/v2/nations/{helpers.apikey()}/&alliance_id={alliance_id}&alliance_position=2,3,4,5&v_mode=false&min_cities={min_cities}&max_cities={max_cities}"
        data = requests.get(url).json()
        helpers.catch_api_error(data, version=2)
        nations = data['data']
        for nation in nations:
            # map v2 policy code to name
            domestic_policy = helpers.api_v2_dom_policy(nation['domestic_policy'])
            war_policy = helpers.api_v2_war_policy(nation['war_policy'])
            embed = discord.Embed(title=f"{nation['leader']} of {nation['nation']}")
            embed.add_field(name=domestic_policy, value="Domestic Policy", inline=False)
            embed.add_field(name=war_policy, value="War Policy", inline=False)
            await ctx.send(embed=embed)

    @policies.error
    async def policies_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}policies <alliance_id> [min_cities] [max_cities]`")


    @commands.command()
    async def warvis(self, ctx, alliance_ids):
        url = f"https://politicsandwar.com/api/v2/nations/{helpers.apikey()}/&alliance_id={alliance_ids}&alliance_position=2,3,4,5&v_mode=false"
        response = requests.get(url).json()
        if not response['api_request']['success']:
            raise Exception(f"Error fetching v2 nations API for alliances {alliance_ids}")
        nations = response['data']
        by_cities = lambda nation: nation['cities']
        nations.sort(reverse=True, key=by_cities)
        with open("../warvis.csv", "w") as f:
            f.write("ID, Nation, Leader, Alliance, Cities, Score, Def, Off, Beige, Soldiers, Tanks, Planes, Ships\n")
            for nation in nations:
                entry = f"{nation['nation_id']}, {nation['nation']}, {nation['leader']}, {nation['alliance']}, {nation['cities']}, \
{nation['score']}, {nation['defensive_wars']}, {nation['offensive_wars']}, {nation['beige_turns']}, \
{nation['soldiers']}, {nation['tanks']}, {nation['aircraft']}, {nation['ships']}\n"
                f.write(entry)
        await ctx.send(file=discord.File('../warvis.csv'))


    
    @warvis.error
    async def warvis_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}policies <alliance_id> [min_cities] [max_cities]`")


def setup(bot):
    bot.add_cog(Nations(bot))