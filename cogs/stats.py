import discord
from discord.ext import commands
import datetime
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))

import helpers
from helpers import commas as c
from helpers import parse_success_level
from dotenv import load_dotenv

load_dotenv()

moometrics_api_url = os.getenv("MOOMETRICS_API_URL")

str_to_datetime = lambda string: datetime.datetime.strptime(string, '%Y-%m-%d/%H:%M:%S')



def add_stat_fields_to_embed(p1_stat_obj, p2_stat_obj, embed):
    attacker = p1_stat_obj
    defender = p2_stat_obj
    att_soldiers_lost = attacker['soldiers_lost']
    att_tanks_lost = attacker['tanks_lost']
    att_planes_lost = attacker['planes_lost']
    att_ships_lost = attacker['ships_lost']
    att_missiles_used = attacker['missiles_used']
    att_nukes_used = attacker['nukes_used']
    def_soldiers_lost = defender['soldiers_lost']
    def_tanks_lost = defender['tanks_lost']
    def_planes_lost = defender['planes_lost']
    def_ships_lost = defender['ships_lost']
    def_missiles_used = defender['missiles_used']
    def_nukes_used = defender['nukes_used']
    categories_field_str = """Total
    -
    Soldiers
    Tanks
    Planes
    Ships
    Missiles
    Nukes
    Total Units
    -
    Gas
    Muni
    Total Usage
    -
    Money (airstrikes)
    Loot
    Infra"""
    embed.add_field(
        name="-",
        value=categories_field_str,
        inline=True
    )
    attacker_losses_field_str = f"""${c(attacker['total_lost_value'])}
    -
    {att_soldiers_lost}
    {att_tanks_lost}
    {att_planes_lost}
    {att_ships_lost}
    {att_missiles_used}
    {att_nukes_used}
    ${c(round(attacker['soldiers_lost_value']+attacker['tanks_lost_value']+attacker['planes_lost_value']+attacker['ships_lost_value']+attacker['missiles_used_value']+attacker['nukes_used_value'],2))}
    -
    {c(round(attacker['gas_used'],2))}
    {c(round(attacker['muni_used'], 2))}
    ${c(round(attacker['gas_used_value'] + attacker['muni_used_value'],2))}
    -
    ${c(round(attacker['money_casualties'],2))}
    ${c(round(attacker['loot_lost_value'],2))}
    ${c(round(attacker['infra_lost_value'],2))}"""
    embed.add_field(
        name="P1 Lost",
        value=attacker_losses_field_str
    )
    defender_losses_field_str = f"""${c(defender['total_lost_value'])}
    -
    {def_soldiers_lost}
    {def_tanks_lost}
    {def_planes_lost}
    {def_ships_lost}
    {def_missiles_used}
    {def_nukes_used}
    ${c(round(defender['soldiers_lost_value']+defender['tanks_lost_value']+defender['planes_lost_value']+defender['ships_lost_value']+defender['missiles_used_value']+defender['nukes_used_value'],2))}
    -
    {c(round(defender['gas_used'],2))}
    {c(round(defender['muni_used'],2))}
    ${c(round(defender['gas_used_value'] + defender['muni_used_value'],2))}
    -
    ${c(round(defender['money_casualties'],2))}
    ${c(round(defender['loot_lost_value'],2))}
    ${c(round(defender['infra_lost_value'],2))}"""
    embed.add_field(
        name="P2 Lost",
        value=defender_losses_field_str
    )
    return embed


class Stats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(helpers.perms_one)
    async def warstats(self, ctx, war_id):
        try:
            war_id = int(war_id)
        except:
            raise Exception("Invalid `war_id`")
        response = requests.get(f"{moometrics_api_url}/wars?id={war_id}")
        data = response.json()
        wars = data['wars']
        if not wars:
            raise Exception("No wars found")
        war = wars[0]
        attacker = war['attacker']
        defender = war['defender']
        embed = add_stat_fields_to_embed(
            attacker,
            defender,
            discord.Embed(
                title = f"{attacker['name']} ({attacker['id']}) vs {defender['name']} ({defender['id']})",
                description = f"{attacker['alliance_name']} vs {defender['alliance_name']} at {war['start_date']}",
                url = f"https://politicsandwar.com/nation/war/timeline/war={war_id}"
            )
        )
        embed.set_footer(text=f"warstats for {war_id} ({war['war_type']})")
        await ctx.send(embed=embed)
        

    @warstats.error
    async def warstats_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}warstats <war_id>`")


    @commands.command()
    async def stats(self, ctx, min_date, max_date, p1_ids, p1_type, p2_ids=None, p2_type=None):
        try:
            if "/" not in min_date:
                min_date += "/00:00:00"
            str_to_datetime(min_date)
        except:
            raise Exception(f"{min_date} is not a valid input for `min_date`")
        if max_date.lower() == "now":
            max_date = str(datetime.datetime.utcnow()).replace(' ', '/').split(".")[0]
        else:
            try:
                if "/" not in max_date:
                    max_date += "/00:00:00"
                str_to_datetime(max_date)
            except:
                raise Exception(f"{max_date} is not a valid input for `max_date`")

        if p1_type not in ['nation', 'alliance']:
            raise Exception(f"{p1_type} is not a valid input for `p1_type`")
        if p2_ids and not p2_type:
            raise Exception("You must specify p2_type")
        if p2_type and p2_type not in ['nation', 'alliance']:
            raise Exception(f"{p2_type} is not a valid input for `p2_type`")
        
        url = f"{moometrics_api_url}/{p1_type}s?most_recent=True&"
        url += '&'.join([f"id={entity}" for entity in p1_ids.split(",")])
        response = requests.get(url)
        p1_data = response.json()[p1_type + "s"]
        if len(p1_data) != len(p1_ids.split(",")):
            raise Exception(f"Not all {p1_type}s with ids {p1_ids} found")

        if p2_ids:
            url = f"{moometrics_api_url}/{p2_type}s?most_recent=True&"
            url += '&'.join([f"id={entity}" for entity in p2_ids.split(",")])
            print(url)
            response = requests.get(url)
            p2_data = response.json()[p2_type + "s"]
            if len(p2_data) != len(p2_ids.split(",")):
                raise Exception(f"Not all {p2_type}s with ids {p2_ids} found")
        else:
            p2_data = []

        # url = f"{moometrics_api_url}/stats?party_1={p1_id}&party_1_type={p1_type}" + \
        #     f"&min_date={min_date}&max_date={max_date}" + \
        #         (f"&party_2={p2_id}&party_2_type={p2_type}" if p2_id and p2_type else "")
        parameters = '&'.join([f"party_1={entity}" for entity in p1_ids.split(",")])
        url = f"{moometrics_api_url}/stats?{parameters}&party_1_type={p1_type}"
        if p2_ids:
            parameters = '&'.join([f"party_2={entity}" for entity in p2_ids.split(",")])
            url += f"&{parameters}&party_2_type={p2_type}"
        url += f"&min_date={min_date}"
        url += f"&max_date={max_date}"
        response = requests.get(url)
        data = response.json()
        p1_stats = data['party_1']
        p2_stats = data['party_2']

        p1_info_string = ", ".join([f"{obj['name']} ({obj['id']})" for obj in p1_data])

        p2_info_string = ", ".join([f"{obj['name']} ({obj['id']})" for obj in p2_data]) if p2_data else "all"

        embed = add_stat_fields_to_embed(
            p1_stats,
            p2_stats,
            discord.Embed(
                title = p1_info_string + " vs " + p2_info_string,
                description = f"From {min_date} to {max_date}"
            )
        )
        # embed.set_footer(text=f"")
        await ctx.send(embed=embed)
        

    @stats.error
    async def stats_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}stats <min_date: yyyy-mm-dd> <max_date: yyyy-mm-dd | now> <p1_id> <p1_type: nation/alliance> [p2_id] [p2_type: nation/alliance]`")


    @commands.command()
    @commands.check(helpers.perms_one)
    async def wars(self, ctx, nation_id):
        try:
            nation_id = int(nation_id)
        except:
            raise Exception("Invalid `war_id`")
        response = requests.get(f"{moometrics_api_url}/wars?involved_nation_id={nation_id}&active=True")
        data = response.json()
        wars = data['wars']
        if not wars:
            raise Exception("No wars found")
        text = "```" + '\n'.join([
            f"{war['id']} | {war['start_date']} | {war['attacker']['name']} attacked {war['defender']['name']} | {war['war_type']}" for war in wars
        ]) + "```"
        await ctx.send(text)
        
    @wars.error
    async def wars_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}wars <nation_id>`")


    
    @commands.command()
    @commands.check(helpers.perms_one)
    async def warattacks(self, ctx, war_id):
        try:
            war_id = int(war_id)
        except:
            raise Exception("Invalid `war_id`")
        response = requests.get(f"{moometrics_api_url}/attacks?war_id={war_id}")
        data = response.json()
        attacks = data['attacks']
        if not attacks:
            raise Exception("No attacks found")
        text = "```" + '\n'.join([
            f"{attack['id']} | {attack['date_time']} | {attack['attacker']['name']} attacked {attack['defender']['name']} | {attack['attack_type']} | {parse_success_level(attack['success'])}" for attack in attacks
        ]) + "```"
        await ctx.send(text)
        
    @warattacks.error
    async def warattacks_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}warattacks <war_id>`")




def setup(bot):
    bot.add_cog(Stats(bot))