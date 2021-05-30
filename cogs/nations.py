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
    @commands.check(helpers.perms_nine)
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
                entry = f"https://politicsandwar.com/nation/id={nation['nation_id']}, {nation['nation']}, {nation['leader']}, {nation['alliance']}, {nation['cities']}, \
{nation['score']}, {nation['defensive_wars']}, {nation['offensive_wars']}, {nation['beige_turns']}, \
{nation['soldiers']}, {nation['tanks']}, {nation['aircraft']}, {nation['ships']}\n"
                f.write(entry)
        await ctx.send(file=discord.File('../warvis.csv'))

    @warvis.error
    async def warvis_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}policies <alliance_id> [min_cities] [max_cities]`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def raidfinder(self, ctx, min_score, max_score, min_loot, max_beige_turns, min_open_slots, results):
        if int(results) > 30:
            raise Exception("Too many results selected, max is 30")
        # disallowed_alliances = ["7450"]
        # disallowed_alliances_query = " OR ".join(disallowed_alliances)
        # AND NOT ({disallowed_alliances_query})
        def prettify_loot(text):
            text = text.replace('\r\n', '')
            while '  ' in text:
                text = text.replace('  ', ' ')
            return text
        if ctx.guild.id == 700094396653240341:
            query = f"SELECT * FROM raids WHERE score >= ? AND score <= ? AND total_loot_value > ? AND beige_turns <= ? AND open_slots >= ? ORDER BY total_loot_value DESC LIMIT ?"
        else:
            query = f"SELECT * FROM raids WHERE score >= ? AND score <= ? AND total_loot_value > ? AND beige_turns <= ? AND open_slots >= ? AND alliance_id = 0 ORDER BY total_loot_value DESC LIMIT ?"

        result = helpers.read_query('databases/raids.sqlite', query, (min_score, max_score, min_loot, max_beige_turns, min_open_slots, results))
        await ctx.send(f"**{len(result)}** nations found")
        for entry in result:
            text = f"""https://politicsandwar.com/nation/id={entry[0]}
Looted in war type **{entry[3]}** on **{entry[6]}**
Beige Loot: {prettify_loot(entry[7])}
Alliance Loot: {prettify_loot(entry[9])}
Total Value: **${'{:,}'.format(entry[-1])}**
**{entry[2]}** Beige Turns
**{entry[4]}** Open Def Slots
-----
            """
            await ctx.send(text)
        await ctx.send(f"Done, {len(result)} nations found")

    @raidfinder.error
    async def raidfinder_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}raidfinder <score> <min_loot>`")


def setup(bot):
    bot.add_cog(Nations(bot))