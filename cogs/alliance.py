import discord
from discord.ext import commands
import requests
import datetime
import concurrent.futures
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))

from cogs.calculations import nation_income_one_city
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
        raise Exception("Nope")
        return
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
                nations(first: 500,alliance_id:%s,vmode:false,
                        min_cities:%s,max_cities:%s) {
                    data {id,num_cities,nation_name,leader_name,alliance_position,last_active
                        offensive_wars{id,def_alliance_id,turnsleft}
                    }
                }
            }""" % (str(alliance_id), str(min_cities), str(max_cities))
        result = requests.post(url,json={'query':query}).json()['data']['nations']['data']
        for nation in result:
            if nation['alliance_position'] == "APPLICANT":
                continue
            active_wars = [war for war in nation['offensive_wars'] if war['turnsleft'] > 0]
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
            embed.set_footer(text=f"Last Active: {nation['last_active']}")
            await ctx.send(embed=embed)

    @raids.error
    async def raids_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}raids <alliance_id> [min_cities] [max_cities]`")

    @commands.command()
    @commands.check(helpers.perms_six)
    async def usage(self, ctx, days, min_cities=0, max_cities=100):
        try:
            days = int(days)
        except:
            raise Exception("Invalid selection for <days>")
        data = helpers.get_data()
        alliance_id = data["discord_to_alliance"][str(ctx.guild.id)]
        url = f"https://politicsandwar.com/api/alliance-members/?allianceid={alliance_id}&key={helpers.apikey(alliance_id=alliance_id, bank_access=True)}"
        data = requests.get(url).json()
        if not data['success']:
            raise Exception("Error fetching data from alliance-members endpoint")
        nations = data['nations']
        for nation in nations:
            cities = nation['cities']
            if cities > max_cities or cities < min_cities:
                continue
            if float(nation['coal']) == -1:
                embed = discord.Embed(title=f"{nation['nation']} - Not showing resources", description=f"c{cities} in {nation['alliance']}")
                await ctx.send(embed=embed)
                continue
            income_data, nation_data = nation_income_one_city(nation['nationid'])
            gross_cash, upkeep, food_production, food_consumption, net_coal, net_oil, net_uranium, \
                net_lead, net_iron, net_bauxite, net_gasoline, net_munitions, net_steel, net_aluminum = income_data
            net_food = round(food_production - food_consumption)
            coal = float(nation['coal'])
            oil = float(nation['oil'])
            uranium = float(nation['uranium'])
            lead = float(nation['lead'])
            iron = float(nation['iron'])
            bauxite = float(nation['bauxite'])
            food = float(nation['food'])
            def n_or_zero(n):
                if n > 0:
                    return n
                else:
                    return 0
            def needed(current, net):
                if net > 0:
                    return 0
                else:
                    return n_or_zero(round(((net*days) * -1) - current))
            coal_needed = needed(coal, net_coal)
            oil_needed = needed(oil, net_oil)
            uranium_needed = needed(uranium, net_uranium)
            lead_needed = needed(lead, net_lead)
            iron_needed = needed(iron, net_iron)
            bauxite_needed = needed(bauxite, net_bauxite)
            food_needed = needed(food, net_food)
            c = helpers.commas
            embed = discord.Embed(title=nation['nation'], description=f"c{cities} in {nation['alliance']}")
            if net_coal < 0 and coal_needed > 0:
                embed.add_field(name=f"{c(coal_needed)} Coal", value=f"{c(round(net_coal))} usage \n \
                        (has {c(coal)} / {round(coal/(net_coal*-1),1)} days)")
            if net_oil < 0 and oil_needed > 0:
                embed.add_field(name=f"{c(oil_needed)} Oil", value=f"{c(round(net_oil))} usage \n \
                        (has {c(oil)} / {round(oil/(net_oil*-1),1)} days)")
            if net_uranium < 0 and uranium_needed > 0:
                embed.add_field(name=f"{c(uranium_needed)} Uranium", value=f"{c(round(net_uranium))} usage \n \
                        (has {c(uranium)} / {round(uranium/(net_uranium*-1),1)} days)")
            if net_lead < 0 and lead_needed > 0:
                embed.add_field(name=f"{c(lead_needed)} Lead", value=f"{c(round(net_lead))} usage \n \
                        (has {c(lead)} / {round(lead/(net_lead*-1),1)} days)")
            if net_iron < 0 and iron_needed > 0:
                embed.add_field(name=f"{c(iron_needed)} Iron", value=f"{c(round(net_iron))} usage \n \
                        (has {c(iron)} / {round(iron/(net_iron*-1),1)} days)")
            if net_bauxite < 0 and bauxite_needed > 0:
                embed.add_field(name=f"{c(bauxite_needed)} Bauxite", value=f"{c(round(net_bauxite))} usage \n \
                        (has {c(bauxite)} / {round(bauxite/(net_bauxite*-1),1)} days)")
            if net_food < 0 and food_needed > 0:
                embed.add_field(name=f"{c(food_needed)} Food", value=f"{c(round(net_food))} usage \n \
                        (has {c(food)} / {round(food/(net_food*-1),1)} days)")
            await ctx.send(embed=embed)
        await ctx.send("All nations displayed")

    @usage.error
    async def usage_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}usage [min_cities] [max_cities]`")


    @commands.command()
    @commands.check(helpers.perms_six)
    async def checkraws(self, ctx, min_cities, max_cities):
        data = helpers.get_data()
        alliance_id = data["discord_to_alliance"][str(ctx.guild.id)]
        url = f"https://politicsandwar.com/api/alliance-members/?allianceid={alliance_id}&key={helpers.apikey(alliance_id=alliance_id)}"
        nations = requests.get(url).json()
        try:
            if nations['general_message']: raise RuntimeError(nations['general_message'])
        except: pass
        nations = nations['nations']
        for nation in nations:
            cities = nation['cities']
            if int(cities) < int(min_cities) or int(cities) > int(max_cities): continue
            nation_id = nation['nationid']
            income_data, nation_data = nation_income_one_city(nation_id)
            gross_cash, upkeep, food_production, food_consumption, net_coal, net_oil, net_uranium, \
                net_lead, net_iron, net_bauxite, net_gasoline, net_munitions, net_steel, net_aluminum = income_data
            net_food = round(food_production - food_consumption)
            data = {
            'coal':{'current':float(nation['coal']),'net':net_coal},
            'oil':{'current':float(nation['oil']),'net':net_oil},
            'lead':{'current':float(nation['lead']),'net':net_lead},
            'iron':{'current':float(nation['iron']),'net':net_iron},
            'bauxite':{'current':float(nation['bauxite']),'net':net_bauxite},
            'food':{'current':float(nation['food']),'net':net_food},
            'uranium':{'current':float(nation['uranium']),'net':net_uranium}
            }
            message = f"""```
__{nation['leader']} of {nation['nation']} ({nation_id}) - c{nation['cities']}__
"""
            display = False
            for resource in ['coal','oil','iron','lead','bauxite','food','uranium']:
                resource_data = data[resource]
                if resource_data['net'] >= 0: continue
                else: pass
                display = True
                message += f"{resource}: has {'{:,}'.format(resource_data['current'])}, is using {'{:,}'.format(round(resource_data['net'],2))}\n"
            message+='\n```'
            if display:
                await ctx.send(message)


    @checkraws.error
    async def checkraws_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}checkraws <min_cities> <max_cities>`")


    @commands.command()
    @commands.check(helpers.perms_one)
    async def bankbyloot(self, ctx, alliance_id):
        key = helpers.apikey()
        wars = requests.get("http://politicsandwar.com/api/wars/5000&alliance_id=%s&key=%s" % (str(alliance_id),key)).json()["wars"]
        alliance_info = requests.get("http://politicsandwar.com/api/alliance/id=%s&key=%s" % (alliance_id,key)).json()
        try:
            if alliance_info['error'] and "api" not in alliance_info['error'].lower():
                await ctx.send("Error fetching alliance data")
                return
        except:
            pass
        alliance_name = alliance_info['name']
        if len(wars) < 1:
            defeat = None
        for war in wars:
            if (war["status"] == "Attacker Victory" and war["defenderAA"] == alliance_name) or (war["status"] == "Defender Victory" and war["attackerAA"] == alliance_name):
                defeat = war["warID"]
        if defeat is not None:
            beige = requests.get("http://politicsandwar.com/api/war-attacks/key=%s&war_id=%s" % (key,defeat)).json()["war_attacks"]
            alliance_loot = beige[0]["note"].replace('\n', ' ').replace('\r', '').replace('                                              ',' ')
            percent = float(alliance_loot.split('%')[0].split('looted ')[1])
            try:
                multiply_by = 100/percent
            except:
                multiply_by = 100/0.01
            date = beige[0]["date"]
            cash = int(alliance_loot.split("$")[1].split(", ")[0].replace(",",""))*multiply_by
            coal = int(alliance_loot.split(" Coal")[0].split(", ")[2].replace(",",""))*multiply_by
            oil = int(alliance_loot.split(" Oil")[0].split(", ")[3].replace(",",""))*multiply_by
            uranium = int(alliance_loot.split(" Uranium")[0].split(", ")[4].replace(",",""))*multiply_by
            iron = int(alliance_loot.split(" Iron")[0].split(", ")[5].replace(",",""))*multiply_by
            bauxite = int(alliance_loot.split(" Bauxite")[0].split(", ")[6].replace(",",""))*multiply_by
            lead = int(alliance_loot.split(" Lead")[0].split(", ")[7].replace(",",""))*multiply_by
            gasoline = int(alliance_loot.split(" Gasoline")[0].split(", ")[8].replace(",",""))*multiply_by
            munitions = int(alliance_loot.split(" Munitions")[0].split(", ")[9].replace(",",""))*multiply_by
            steel = int(alliance_loot.split(" Steel")[0].split(", ")[10].replace(",",""))*multiply_by
            aluminum = int(alliance_loot.split(" Aluminum")[0].split(", ")[11].replace(",",""))*multiply_by
            food = int(alliance_loot.split(" Food")[0].split("and ")[-1].replace(",",""))*multiply_by
            info = [alliance_loot,date,cash,coal,oil, uranium, iron, bauxite, lead, gasoline, munitions, steel, aluminum, food]
            embed = discord.Embed(title=("bank of %s" % alliance_id),description=("as of %s" % info[1]))
            embed.add_field(name="cash",value=("{:,}".format(int(info[2]))))
            embed.add_field(name="coal",value=("{:,}".format(int(info[3]))))
            embed.add_field(name="oil",value=("{:,}".format(int(info[4]))))
            embed.add_field(name="uranium",value=("{:,}".format(int(info[5]))))
            embed.add_field(name="iron",value=("{:,}".format(int(info[6]))))
            embed.add_field(name="bauxite",value=("{:,}".format(int(info[7]))))
            embed.add_field(name="lead",value=("{:,}".format(int(info[8]))))
            embed.add_field(name="gasoline",value=("{:,}".format(int(info[9]))))
            embed.add_field(name="munitions",value=("{:,}".format(int(info[10]))))
            embed.add_field(name="steel",value=("{:,}".format(int(info[11]))))
            embed.add_field(name="aluminum",value=("{:,}".format(int(info[12]))))
            embed.add_field(name="food",value=("{:,}".format(int(info[13]))))
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="No defeat found")
            await ctx.send(embed=embed)
    
    @bankbyloot.error
    async def bankbyloot_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}bankbyloot <alliance_id>`")
    


def setup(bot):
    bot.add_cog(Alliance(bot))
