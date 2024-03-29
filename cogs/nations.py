import discord
from discord.ext import commands
import requests
import sys
from bs4 import BeautifulSoup
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))

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
    @commands.check(helpers.perms_seven)
    async def warvisv2(self, ctx, alliance_ids):
        url = f"https://politicsandwar.com/api/v2/nations/{helpers.apikey()}/&alliance_id={alliance_ids}&alliance_position=2,3,4,5&v_mode=false"
        response = requests.get(url).json()
        if not response['api_request']['success']:
            raise Exception(f"Error fetching v2 nations API for alliances {alliance_ids}")
        nations = response['data']
        by_cities = lambda nation: nation['cities']
        nations.sort(reverse=True, key=by_cities)
        with open("../warvis.csv", "w") as f:
            f.write("ID, Nation, Leader, Alliance, Cities, Score, Off, Def, Att1, Att2, Att3, Beige, Soldiers, Tanks, Planes, Ships\n")
            for nation in nations:
                entry = f"https://politicsandwar.com/nation/id={nation['nation_id']}, {nation['nation']}, {nation['leader']}, {nation['alliance']}, {nation['cities']}, \
{nation['score']}, {nation['offensive_wars']}, {nation['defensive_wars']},-,-,-, {nation['beige_turns']}, \
{nation['soldiers']}, {nation['tanks']}, {nation['aircraft']}, {nation['ships']}\n"
                f.write(entry)
        await ctx.send(file=discord.File('../warvis.csv'))

    @warvisv2.error
    async def warvisv2_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}warvisv2 <alliance_ids>`")


    @commands.command()
    @commands.check(helpers.perms_seven)
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
                except:
                    att1 = ""
                # if num_active_def_wars >= 2:
                try:
                    att2_data = active_def_wars[1]['attacker']
                    att2 = round(sum([
                        (att2_data[unit] / (att2_data['num_cities']*cap)) * 100 for unit, cap in unit_max
                    ]) / 4)
                except:
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
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}warvis`")


    @commands.command()
    @commands.check(helpers.perms_two)
    async def raidfinder(self, ctx, min_score, max_score, min_loot, max_beige_turns, min_open_slots, results):
        if int(results) > 30:
            raise Exception("Too many results selected, max is 30")
        # disallowed_alliances = ["7450"]
        # disallowed_alliances_query = " OR ".join(disallowed_alliances)
        # AND NOT ({disallowed_alliances_query})
        with open('/home/pi/Code/Big-Egg-Bot/raidfinder.txt', 'r') as f:
           content = f.read()
        if 'disallow' in content:
            raise Exception("Raidfinder updating, please wait")
        def prettify_loot(text):
            text = text.replace('\r\n', '')
            while '  ' in text:
                text = text.replace('  ', ' ')
            return text
        # bot testing and paragon and frenchm
        if ctx.guild.id == 700094396653240341 or ctx.guild.id == 869424139037990912 or ctx.guild.id == 794032133051645973:
            query = f"SELECT * FROM raids WHERE score >= ? AND score <= ? AND total_loot_value > ? AND beige_turns <= ? AND open_slots >= ? ORDER BY total_loot_value DESC LIMIT ?"
        elif ctx.guild.id == 882831852396748820:
            query = f"SELECT * FROM raids WHERE score >= ? AND score <= ? AND total_loot_value > ? AND beige_turns <= ? AND open_slots >= ? ORDER BY total_loot_value DESC LIMIT ?"
        else:
            query = f"SELECT * FROM raids WHERE score >= ? AND score <= ? AND total_loot_value > ? AND beige_turns <= ? AND open_slots >= ? AND alliance_id = 0 ORDER BY total_loot_value DESC LIMIT ?"

        result = helpers.read_query(query, (min_score, max_score, min_loot, max_beige_turns, min_open_slots, results))
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


    @commands.command()
    @commands.check(helpers.perms_six)
    async def resources(self, ctx, nation_id):
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
        nation = [nation for nation in data['nations'] if nation['nationid'] == nation_id]
        if not nation:
            raise Exception("Nation not found")
        else:
            nation = nation[0]
        if not nation:
            raise Exception(f"No nation by that id found in the alliance {alliance_id}")
        embed = discord.Embed(title=f"{nation['leader']} of {nation['nation']}", \
                description=f"c{nation['cities']} in [{nation['alliance']}](https://politicsandwar.com/alliance/id={nation['allianceid']})", \
                    color=ctx.author.color)
        commas = lambda n: "{:,}".format(n)
        embed.add_field(name=f"${commas(float(nation['money']))}", value="Cash", inline=True)
        embed.add_field(name=f"{commas(float(nation['coal']))}", value="Coal", inline=True)
        embed.add_field(name=f"{commas(float(nation['oil']))}", value="Oil", inline=True)
        embed.add_field(name=f"{commas(float(nation['uranium']))}", value="Uranium", inline=True)
        embed.add_field(name=f"{commas(float(nation['iron']))}", value="Iron", inline=True)
        embed.add_field(name=f"{commas(float(nation['lead']))}", value="Lead", inline=True)
        embed.add_field(name=f"{commas(float(nation['bauxite']))}", value="Bauxite", inline=True)
        embed.add_field(name=f"{commas(float(nation['gasoline']))}", value="Gasoline", inline=True)
        embed.add_field(name=f"{commas(float(nation['munitions']))}", value="Munitions", inline=True)
        embed.add_field(name=f"{commas(float(nation['steel']))}", value="Steel", inline=True)
        embed.add_field(name=f"{commas(float(nation['aluminum']))}", value="Aluminum", inline=True)
        embed.add_field(name=f"{commas(float(nation['food']))}", value="Food", inline=True)
        embed.add_field(name=f"{commas(int(nation['credits']))}", value="Credits", inline=True)
        embed.set_footer(text=f"{nation['offensivewars']} off wars | {nation['defensivewars']} def wars | {nation['minutessinceactive']} min since active")
        await ctx.send(embed=embed)

    @resources.error
    async def resources_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}resources <nation_id>`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def timers(self, ctx, alliance_ids, min_cities=0, max_cities=100):
        key = helpers.apikey()
        helpers.check_city_inputs(min_cities, max_cities)
        url = f"https://politicsandwar.com/api/v2/nations/{key}/&alliance_id={alliance_ids}&alliance_position=2,3,4,5&v_mode=false&min_cities={min_cities}&max_cities={max_cities}"
        response = requests.get(url).json()
        nations = response['data']
        for nation in nations:
            url = f"https://politicsandwar.com/api/nation/id={nation['nation_id']}&key={key}"
            nation_data = requests.get(url).json()
            embed = discord.Embed(title=f"{nation_data['leadername']} of {nation_data['name']}", \
                    description=f"[{nation_data['alliance']}](https://politicsandwar.com/alliance/id={nation_data['allianceid']}) c{nation_data['cities']}", \
                        url=f"https://politicsandwar.com/nation/id={nation['nation_id']}")
            embed.add_field(name=f"{max(120-nation_data['turns_since_last_city'],0)} turns", value="City Timer")
            embed.add_field(name=f"{max(120-nation_data['turns_since_last_project'],0)} turns", value="Project Timer")
            embed.set_footer(text=f"Policy: {nation_data['domestic_policy']}")
            await ctx.send(embed=embed)


    @timers.error
    async def timers_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}timers <alliance_ids>`")


    @commands.command(aliases=["timers2"])
    @commands.check(helpers.perms_six)
    async def uglytimers(self, ctx, alliance_ids, min_cities=0, max_cities=100):
        key = helpers.apikey()
        helpers.check_city_inputs(min_cities, max_cities)
        url = f"https://politicsandwar.com/api/v2/nations/{key}/&alliance_id={alliance_ids}&alliance_position=2,3,4,5&v_mode=false&min_cities={min_cities}&max_cities={max_cities}"
        response = requests.get(url).json()
        nations = response['data']
        for nation in nations:
            url = f"https://politicsandwar.com/api/nation/id={nation['nation_id']}&key={key}"
            nation_data = requests.get(url).json()
            msg = f"""```
{nation_data['leadername']} of {nation_data['name']} (c{nation_data['cities']})
{max(120-nation_data['turns_since_last_city'],0)} city timer turns
{max(120-nation_data['turns_since_last_project'],0)} project timer turns```"""
            await ctx.send(msg)


    @uglytimers.error
    async def uglytimers_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}uglytimers <alliance_ids>`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def policies(self, ctx, alliance_id, min_cities=0, max_cities=100):
        try:
            alliance_id = int(alliance_id)
        except:
            raise Exception("Invalid alliance id")
        helpers.check_city_inputs(min_cities, max_cities)
        url = f"https://politicsandwar.com/api/v2/nations/{helpers.apikey()}/&alliance_id={alliance_id}&alliance_position=2,3,4,5&v_mode=false&min_cities={min_cities}&max_cities={max_cities}"
        data = requests.get(url).json()
        helpers.catch_api_error(data, version=2)
        nations = data['data']
        for nation in nations:
            # map v2 policy code to name
            domestic_policy = helpers.api_v2_dom_policy(nation['domestic_policy'])
            war_policy = helpers.api_v2_war_policy(nation['war_policy'])
            embed = discord.Embed(title=f"{nation['leader']} of {nation['nation']}", \
                    description=f"[{nation['alliance']}](https://politicsandwar.com/alliance/id={nation['alliance_id']}) c{nation['cities']}", \
                        url=f"https://politicsandwar.com/nation/id={nation['nation_id']}")
            embed.add_field(name=domestic_policy, value="Domestic Policy", inline=False)
            embed.add_field(name=war_policy, value="War Policy", inline=False)
            await ctx.send(embed=embed)

    @policies.error
    async def policies_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}policies <alliance_id> [min_cities] [max_cities]`")


    @commands.command()
    async def nsearch(self, ctx, query):
        url = ("https://politicsandwar.com/index.php?id=15&keyword=" + query + "&cat=everything&ob=score&od=DESC&backpage=%3C%3C&maximum=3&minimum=0")
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.find('table',class_="nationtable")
        results = table.find_all('td')
        results_displayed = 0
        for result in results:
            if results_displayed == 3:
                break
            try:
                link = result.find('a').get('href')
                nation = result.text.split('\n')[1]
                leader = result.text.split('\r')[1].replace('  ','').replace('\n','').replace('\n','')
                results_displayed += 1
                await ctx.send(f"{leader}of {nation} - {link}")
            except:
                continue

    @nsearch.error
    async def nsearch_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}nsearch <query>`")


    @commands.command()
    @commands.check(helpers.perms_seven)
    async def nationsheet(self, ctx, alliance_ids):
        url = f"https://politicsandwar.com/api/v2/nations/{helpers.apikey()}/&alliance_id={alliance_ids}&alliance_position=2,3,4,5&v_mode=false"
        data = requests.get(url).json()['data']
        data.sort(key=lambda n: n['cities'], reverse=True)
        with open("./nationsheet.csv", 'w') as f:
            for nation in data:
                # nation_id, leader, nation, alliance, city, score, off war range, def war range, since_active, policy, beige, vm turns, beige, off wars, def wars, soldiers, tanks, planes, ships, link
                entry = f"{nation['nation_id']},{nation['leader']},{nation['nation']},{nation['alliance']},{nation['cities']},{nation['score']},{int(round(nation['score']*0.75,0))} - {int(round(nation['score']*1.75,0))},{int(round(nation['score']/1.75,0))} - {int(round(nation['score']/0.75,0))},,{nation['war_policy']},{nation['beige_turns']},{nation['v_mode_turns']},{nation['offensive_wars']},{nation['defensive_wars']},{nation['soldiers']}, {nation['tanks']},{nation['aircraft']},{nation['ships']},https://politicsandwar.com/nation/id={nation['nation_id']}\n"
                f.write(entry)
        instructions = """
1. Download the following file
2. Remove current nation entries
3. Select cell A2
4. Go to the help menu and type to find 'import file' then select it
5. Go to upload and press select file
6. Find the file on your computer and select it
7. Change 'create new spreadsheet' to 'replace data and current cell'
8. Press import data"""
        await ctx.send(instructions)
        await ctx.send(file=discord.File('./nationsheet.csv'))

    @nationsheet.error
    async def nationsheet_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}nationsheet <alliance ids: comma separated, no spaces>`")


    @commands.command()
    @commands.check(helpers.perms_seven)
    async def nationsheet2(self, ctx, alliance_ids):
        url = f"https://politicsandwar.com/api/v2/nations/{helpers.apikey()}/&alliance_id={alliance_ids}&alliance_position=2,3,4,5&v_mode=false"
        data = requests.get(url).json()['data']
        data.sort(key=lambda n: n['cities'], reverse=True)
        with open("./nationsheet2.csv", 'w') as f:
            for nation in data:
                score = nation['score']
                # nation_id, leader, nation, alliance, link, cities, def range, off range, policy, beige, activity, total infra, def wars, off wars, soldiers, tanks, planes, ships, missiles, nukes, vm, planes per city, tanks per city
                entry = f"{nation['nation_id']},{nation['leader']},{nation['nation']},{nation['alliance']},https://politicsandwar.com/nation/id={nation['nation_id']},{nation['cities']},{round(score/1.75)} - {round(score/0.75)},{round(score*0.75)} - {round(score*1.75)},{helpers.api_v2_war_policy(nation['war_policy'])},{nation['beige_turns']},{nation['last_active']},n/a,{nation['defensive_wars']},{nation['offensive_wars']},{nation['soldiers']},{nation['tanks']},{nation['aircraft']},{nation['ships']},{nation['missiles']},{nation['nukes']},{nation['v_mode_turns']},{round(nation['aircraft']/nation['cities'],1)},{round(nation['tanks']/nation['cities'],1)}\n"
                f.write(entry)
        await ctx.send(file=discord.File('./nationsheet2.csv'))

    @nationsheet2.error
    async def nationsheet2_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}nationsheet2 <alliance ids: comma separated, no spaces>`")



def setup(bot):
    bot.add_cog(Nations(bot))