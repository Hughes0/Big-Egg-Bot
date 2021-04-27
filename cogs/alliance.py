import discord
from discord.ext import commands
import requests
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
        if not response['success']:
            raise ValueError("An error occurred fetching data from the API")
        activity = [nation['minutessinceactive'] for nation in nations if nation['vacmode'] == 0]
        notable_times = [ # inclusive
            (0, 0, "currently online"),
            (1, 60, "last hour"),
            (61, 360, "last 12 hours"),
            (361, 1440, "last day"),
            (1441, 4320, "last 3 days")
        ]
        embed = discord.Embed(title=f"Activity Distribution of {nations[0]['alliance']}")
        for (minimum, maximum, label) in notable_times:
            embed.add_field(name=len([n for n in activity if maximum >= n >= minimum]), value=label.capitalize(), inline=False)
        await ctx.send(embed=embed)

    @activity.error
    async def activity_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}activity <alliance id>`")


def setup(bot):
    bot.add_cog(Alliance(bot))