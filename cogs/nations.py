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
        url = f"https://api.politicsandwar.com/graphql?api_key={helpers.apikey(owner='hughes')}"
        by_cities = lambda nation: nation['num_cities']
        nations = []
        has_more_pages = True
        page = 1
        while has_more_pages:
            query = """query {
                nations (first:100, alliance_id:[%s], vmode: false, page: %s) {
                    paginatorInfo {
                        hasMorePages
                    }
                    data {
                        id
                        nation_name
                        leader_name
                        alliance {
                            name
                        }
                        alliance_position
                        num_cities
                        score
                        defensive_wars {
                            turnsleft
                            attacker {
                                soldiers
                                tanks
                                aircraft
                                ships
                                num_cities
                            }
                        }
                        offensive_wars {turnsleft}
                        beigeturns
                        soldiers
                        tanks
                        aircraft
                        ships
                    }
                }
            }""" % (alliance_ids, str(page))
            page += 1
            data = requests.post(url,json={'query':query}).json()['data']['nations']
            has_more_pages = data['paginatorInfo']['hasMorePages']
            nations.extend([nation for nation in data['data'] if nation['alliance_position'] != "APPLICANT"])
        nations.sort(reverse=True, key=by_cities)
        with open("../warvis.csv", "w") as f:
            f.write("ID, Nation, Leader, Alliance, Cities, Score, Off, Def, Att1, Att2, Att3, Beige, Soldiers, Tanks, Planes, Ships\n")
            for nation in nations:
                def_wars = nation['defensive_wars']
                active_def_wars = [war for war in def_wars if war['turnsleft'] > 0]
                num_active_def_wars = len(active_def_wars)
                unit_max = [('soldiers', 15000), ('tanks', 1250), ('aircraft', 75), ('ships', 15)]
                # if num_active_def_wars >= 1:
                try:
                    att1_data = active_def_wars[0]['attacker']
                    att1 = round(sum([
                        (att1_data[unit] / (att1_data['num_cities']*cap)) * 100 for unit, cap in unit_max
                    ]) / 4)
                except Exception as e:
                    att1 = ""
                # if num_active_def_wars >= 2:
                try:
                    att2_data = active_def_wars[1]['attacker']
                    att2 = round(sum([
                        (att2_data[unit] / (att2_data['num_cities']*cap)) * 100 for unit, cap in unit_max
                    ]) / 4)
                except Exception as e:
                    att2 = ""
                # if num_active_def_wars >= 3:
                try:
                    att3_data = active_def_wars[2]['attacker']
                    att3 = round(sum([
                        (att3_data[unit] / (att3_data['num_cities']*cap)) * 100 for unit, cap in unit_max
                    ]) / 4)
                except:
                    att3 = ""
                off_wars = nation['offensive_wars']
                entry = f"https://politicsandwar.com/nation/id={nation['id']}, {nation['nation_name']}, \
{nation['leader_name']}, {nation['alliance']['name']}, {nation['num_cities']}, {nation['score']}, \
{len([war for war in off_wars if war['turnsleft'] > 0])}, \
{len([war for war in def_wars if war['turnsleft'] > 0])}, {att1}, {att2}, {att3},\
{nation['beigeturns']}, {nation['soldiers']}, {nation['tanks']}, \
{nation['aircraft']}, {nation['ships']}\n"
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