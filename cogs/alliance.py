import discord
from discord.ext import commands
import requests
import datetime
import random
import concurrent.futures
import sys
sys.path.append("..")
import helpers



class Alliance(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    
    @commands.group(invoke_without_command=True)
    @commands.check(helpers.perms_six)
    async def militarization(self, ctx, alliance_ids, min_cities=0, max_cities=100):
        # check if inputs are valid
        helpers.check_city_inputs(min_cities, max_cities)
        nations = []
        has_more_pages = True
        page = 1
        apikey = helpers.apikey(owner="hughes")
        url = f"https://api.politicsandwar.com/graphql?api_key={apikey}"
        query = "query{alliances(first:50, id:[%s]) {data {name}}}" % alliance_ids
        alliances = requests.post(url,json={'query':query}).json()['data']['alliances']['data']
        alliance_names = [alliance['name'] for alliance in alliances]
        while has_more_pages:
            query = """query{nations(first:500, alliance_id: [%s] ,min_cities: %s,max_cities:%s, page:%s) {
                paginatorInfo {hasMorePages,lastPage}
                data {id, alliance_position, nation_name, leader_name, num_cities, soldiers, tanks, 
                aircraft, ships, vmode
                cities {barracks, factory, airforcebase, drydock
                }}}}""" % (alliance_ids, str(min_cities), str(max_cities), str(page))
            data = requests.post(url,json={'query':query}).json()['data']['nations']
            has_more_pages = data['paginatorInfo']['hasMorePages']
            nations.extend(data['data'])
            page += 1
        total_cities = 0
        total_barracks = 0
        total_factories = 0
        total_hangars = 0
        total_drydocks = 0
        total_soldiers = 0
        total_tanks = 0
        total_planes = 0
        total_ships = 0
        total_nations = 0
        for nation in nations:
            if nation['alliance_position'] == "APPLICANT" or nation['vmode'] > 0:
                continue
            total_nations += 1
            cities = nation['num_cities']
            soldiers = nation['soldiers']
            tanks = nation['tanks']
            planes = nation['aircraft']
            ships = nation['ships']
            barracks = sum([city['barracks'] for city in nation['cities']])
            factories = sum([city['factory'] for city in nation['cities']])
            hangars = sum([city['airforcebase'] for city in nation['cities']])
            drydocks = sum([city['drydock'] for city in nation['cities']])
            total_cities += cities
            total_barracks += barracks
            total_factories += factories
            total_hangars += hangars
            total_drydocks += drydocks
            total_soldiers += soldiers
            total_tanks += tanks
            total_planes += planes
            total_ships += ships
        embed = discord.Embed(title=', '.join(alliance_names) + " Militarization", description=f"Avg Imps: \
                {round(total_barracks/total_cities,1)} / \
                {round(total_factories/total_cities,1)} / \
                {round(total_hangars/total_cities,1)} / \
                {round(total_drydocks/total_cities,1)}")
        embed.add_field(name="Total", value=f"""{'{:,}'.format(total_soldiers)}
                {'{:,}'.format(total_tanks)}
                {'{:,}'.format(total_planes)}
                {'{:,}'.format(total_ships)}""", inline=True)
        embed.add_field(name="Average", value=f"""{'{:,}'.format(int(round(total_soldiers/total_nations,0)))}
                {'{:,}'.format(int(round(total_tanks/total_nations,0)))}
                {'{:,}'.format(int(round(total_planes/total_nations,0)))}
                {'{:,}'.format(int(round(total_ships/total_nations,0)))}""", inline=True)
        embed.add_field(name="Percent", value=f"""{round((total_soldiers/(total_cities*15000))*100,1)}%
                {round((total_tanks/(total_cities*1250))*100,1)}%
                {round((total_planes/(total_cities*75))*100,1)}%
                {round((total_ships/(total_cities*15))*100,1)}%""", inline=True)
        embed.set_footer(text=f"{total_nations} nations from c{min_cities} - c{max_cities}")
        await ctx.send(embed=embed)

    @militarization.command()
    async def planes(self, ctx, min_cities=0, max_cities=100):
        apikey = helpers.apikey()
        # get top 50 alliances
        url = f"https://politicsandwar.com/api/alliances/?key={apikey}"
        response = requests.get(url).json()
        helpers.catch_api_error(response, version=1)
        alliances = response['alliances'][:30]
        ids = [alliance['id'] for alliance in alliances]
        # get nations from top 50 alliances
        url = f"https://politicsandwar.com/api/v2/nations/{apikey}/&alliance_id={','.join(ids)} \
                &alliance_position=2,3,4,5&v_mode=false&min_cities={min_cities}&max_cities={max_cities}"
        nations = requests.get(url).json()
        helpers.catch_api_error(nations, version=2)
        nations = nations['data']
        alliance_data = []
        for alliance in alliances:
            alliance_id = str(alliance['id'])
            members = [nation for nation in nations if int(nation['alliance_id'] == int(alliance_id))]
            total_planes = sum([member['aircraft'] for member in members])
            total_cities = max(sum(member['cities'] for member in members), 1)
            alliance_data.append({
                "name": alliance['name'],
                "total_planes": total_planes,
                "percent_planes": total_planes / (total_cities * 75)
            })
        by_plane_percent = lambda nation: nation['percent_planes']
        alliance_data.sort(key=by_plane_percent, reverse=True)
        text = "```\n"
        text += "".join([f"Alliance (c{min_cities} - c{max_cities})".ljust(35), "%".ljust(9), "total".ljust(9), "\n"])
        for alliance in alliance_data[:30]:
            text += "".join([alliance['name'].ljust(35), \
                    str(round(alliance['percent_planes']*100,1)).ljust(9), \
                    str('{:,}'.format(alliance['total_planes'])).ljust(9), "\n"])
        text += "\n```"
        await ctx.send(text)
        # calculate militarization from there

        

    @militarization.error
    async def militarization_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}militarization <alliance_id(s)> [min_cities] [max_cities]`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def aaspies(self, ctx, alliance_id, min_cities=0, max_cities=100):
        # check if inputs are valid
        helpers.check_city_inputs(min_cities, max_cities)
        # get alliance id from server id from keys.json
        data = helpers.get_data()
        try:
            discord_alliance_id = data["discord_to_alliance"][str(ctx.guild.id)]
        except KeyError:
            discord_alliance_id = None
        if discord_alliance_id == int(alliance_id):
            # get alliance-members API data
            apikey = helpers.apikey(alliance_id=discord_alliance_id, bank_access=True)
            url = f"https://politicsandwar.com/api/alliance-members/?allianceid={discord_alliance_id}&key={apikey}"
            data = requests.get(url).json()
            # catch API errors
            helpers.catch_api_error(data=data, version=1)
            nations = data['nations']
            nations = [nation for nation in nations if nation['cities'] >= min_cities and nation['cities'] <= max_cities]
        else:
            await ctx.send("Calculating, this could take a while...")
            url = f"https://api.politicsandwar.com/graphql?api_key={helpers.apikey(owner='hughes')}"
            query = """query{
                nations(first:500,alliance_id:%s,min_cities:%s,max_cities:%s,vmode:false) {
                    data {
                        id, nation_name, num_cities, cia, warpolicy
                        alliance {name}
                    }
                }
            }""" % (str(alliance_id), str(min_cities), str(max_cities))
            data = requests.post(url,json={'query':query}).json()['data']['nations']['data']
            ids = [nation['id'] for nation in data]
            policies = [nation['warpolicy'] for nation in data]
            with concurrent.futures.ProcessPoolExecutor() as executor:
                spies = executor.map(helpers.spies, ids, policies)
            spies = [spy for spy in spies]
            nations = [
                        {
                            "nation": data[i]['nation_name'],
                            "alliance": data[i]['alliance']['name'],
                            "intagncy": data[i]['cia'],
                            "cities": data[i]['num_cities'],
                            "spies": spies[i]
                        } for i in range(len(spies))
                    ]
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
                if nation['intagncy'] == "1" or nation['intagncy'] == True:
                    max_spies = 60
                else:
                    max_spies = 50
                embed.add_field(name=f"{nation['nation']} c{nation['cities']}", value=f"{nation['spies']} / {max_spies}")
            embed.set_footer(text=f"Page {page}")
            await ctx.send(embed=embed)
            page += 1
        await ctx.send("All results displayed")

    @aaspies.error
    async def aaspies_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}aaspies <alliance_id> [min_cities] [max_cities]`")


    @commands.command()
    @commands.check(helpers.perms_one)
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
            embed.add_field(name=str(raw), value=label.capitalize(), inline=False)
        await ctx.send(embed=embed)

    @activity.error
    async def activity_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}activity <alliance id>`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def counters(self, ctx, att_nation_id, def_alliance_id=None):
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
            embed = discord.Embed(title=f"{nation['leader']} of {nation['nation']}")
            embed.add_field(name=domestic_policy, value="Domestic Policy", inline=False)
            embed.add_field(name=war_policy, value="War Policy", inline=False)
            await ctx.send(embed=embed)

    @policies.error
    async def policies_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}policies <alliance_id> [min_cities] [max_cities]`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def infra(self, ctx, alliance_id, min_cities=0, max_cities=100):
        try:
            alliance_id = int(alliance_id)
        except:
            raise Exception("Invalid alliance id")
        helpers.check_city_inputs(min_cities, max_cities)
        query = """
            query{
                nations(first: 500,alliance_id:%s,vmode:false,
                        min_cities:%s,max_cities:%s) {
                    data {id,num_cities,nation_name,leader_name,alliance_position
                        cities {infrastructure}
                    }
                }
            }""" % (str(alliance_id), str(min_cities), str(max_cities))
        url = f"https://api.politicsandwar.com/graphql?api_key={helpers.apikey(owner='hughes')}"
        result = requests.post(url,json={'query':query}).json()['data']['nations']['data']
        for nation in result:
            if nation['alliance_position'] == "APPLICANT":
                continue
            infra_dist = [city['infrastructure'] for city in nation['cities']]
            embed = discord.Embed(title=f"{nation['leader_name']} of {nation['nation_name']}", \
                    description=f"c{nation['num_cities']}", \
                    url=f"https://politicsandwar.com/nation/id={nation['id']}")
            embed.add_field(name=round(sum(infra_dist)/len(infra_dist)), value="Avg Infra")
            embed.add_field(name=max(infra_dist), value="Highest Infra")
            embed.add_field(name=min(infra_dist), value="Lowest Infra")
            # embed.set_footer(text=f"infra for {alliance_id}, c{min_cities} - c{max_cities}")
            await ctx.send(embed=embed)
        await ctx.send("Done")

    @infra.error
    async def infra_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}infra <alliance_id> [min_cities] [max_cities]`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def raids(self, ctx, alliance_id, min_cities=0, max_cities=9):
        try:
            alliance_id = int(alliance_id)
        except:
            raise Exception("Invalid alliance id")
        helpers.check_city_inputs(min_cities, max_cities)
        url = f"https://api.politicsandwar.com/graphql?api_key={helpers.apikey(owner='hughes')}"
        query = """
            query{
                nations(first: 500,alliance_id:7450,vmode:false,
                        min_cities:0,max_cities:9) {
                    data {id,num_cities,nation_name,leader_name,alliance_position
                        offensive_wars{id,def_alliance_id,turnsleft}
                    }
                }
            }"""
        result = requests.post(url,json={'query':query}).json()['data']['nations']['data']
        for nation in result:
            if nation['alliance_position'] == "APPLICANT":
                continue
            active_wars = [war for war in nation['offensive_wars'] if war['turnsleft'] > 0]
            # [name](url)
            embed = discord.Embed(title=f"{nation['leader_name']} of {nation['nation_name']}", \
                    description=f"c{nation['num_cities']} with {len(active_wars)} active wars", \
                    url=f"https://politicsandwar.com/nation/id={nation['id']}")
            if active_wars:
                text = ", ".join([f"[{war['id']}](https://politicsandwar.com/nation/war/timeline/war={war['id']})" for war in active_wars])
                embed.add_field(name="Wars", value=text)
                text = ", ".join([str(war['turnsleft']) for war in active_wars])
                embed.add_field(name="Turns Left", value=text)
                text = ", ".join([war['def_alliance_id'] for war in active_wars])
                embed.add_field(name="Def Alliance", value=text)
            await ctx.send(embed=embed)

    @raids.error
    async def raids_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}raids <alliance_id> [min_cities] [max_cities]`")



def setup(bot):
    bot.add_cog(Alliance(bot))