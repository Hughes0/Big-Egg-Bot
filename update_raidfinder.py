from os import path
import requests
import sqlite3
from sqlite3 import Error
import helpers
import datetime
import json
import time

def parse_loot(text):
    text = text.split('looted')[-1].split("food.")[0].split('alliance bank')[-1]
    text += "food"
    text = text.replace('\r\n', '').lower()
    while '  ' in text:
        text = text.replace('  ', ' ')
    resources = ['coal', 'oil', 'uranium', 'iron', 'bauxite', 'lead', 'gasoline', 'munitions', 'steel', 'aluminum']
    value = 0
    for resource in resources:
        raw_amount = text.split(f" {resource}")[0].split(", ")[-1]
        value += int(raw_amount.replace(',','')) * prices[resource]
    food = text.split(f" food")[0].split("and ")[-1].replace(',','')
    value += int(food) * prices['food']
    cash = text.split("$")[-1].split(", ")[0].replace(',','')
    value += int(cash)
    return value


def check_nation(nation):
    def_wars = nation['defensive_wars']
    if not def_wars:
        return
    # remove active wars
    def_wars = [war for war in def_wars if war['turnsleft'] <= 0]
    # return none if no finished def wars
    if not def_wars:
        return
    # get most recent defeat
    last_defeat = None
    last_defeat_date = datetime.datetime.strptime("0001-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
    for war in def_wars:
        beige_attack = [attack for attack in war['attacks'] if attack['type'] == "VICTORY"]
        if not beige_attack:
            continue
        defeat_date = datetime.datetime.strptime(beige_attack[0]['date'], "%Y-%m-%dT%H:%M:%S+00:00")
        if defeat_date > last_defeat_date:
            last_defeat_date = defeat_date
            last_defeat = war
    if not last_defeat:
        return
    # get winner of war
    winner = last_defeat['winner']
    loser = None
    if last_defeat['attacker']:
        if winner == last_defeat['attacker']['id']:
            # if winner is attacker
            # set nation variables to defender's info
            loser = last_defeat['defender']
    if last_defeat['defender']:
        if winner == last_defeat['defender']['id']:
            # if winner is defender
            # set nation variables to attacker's info
            loser = last_defeat['attacker']
    if not loser:
        return
    open_slots = 3 - len([war for war in loser['defensive_wars'] if war['turnsleft'] > 0])
    # get nation loot
    loot_value = 0
    beige_attack = [attack for attack in last_defeat['attacks'] if attack['type'] == "VICTORY"][0]
    beige_loot = parse_loot(beige_attack['loot_info'])
    loot_value += beige_loot
    bank_attack = [attack for attack in last_defeat['attacks'] if attack['type'] == "ALLIANCELOOT"]
    if bank_attack:
        bank_loot_raw = bank_attack[0]['loot_info']
        bank_loot = parse_loot(bank_loot_raw)
    else:
        bank_attack = "None"
        bank_loot_raw = "None"
        bank_loot = 0
    # if alliance id is not 0 and there is bank loot, add it to the loot value
    if loser['alliance_id'] != "0" and bank_loot:
        loot_value += bank_loot
    # store data: raids
    query = """
        INSERT INTO raids
            (nation_id, score, beige_turns, war_type, open_slots, alliance_id, date_looted, nation_loot_raw, nation_loot_value, bank_loot_raw, bank_loot_value, total_loot_value)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    arguments = (loser['id'], loser['score'], loser['beigeturns'], last_defeat['war_type'], \
            open_slots, loser['alliance_id'], beige_attack['date'], beige_attack['loot_info'], beige_loot, \
            bank_loot_raw, bank_loot, loot_value)
    helpers.execute_query(query, arguments)

def get_wars():
    url = f"https://politicsandwar.com/api/alliances/?key={helpers.apikey()}"
    response = requests.get(url).json()
    if not response['success']:
        raise Exception("Error getting data from alliances API")
    alliance_ids = [int(alliance['id']) for alliance in response['alliances']]
    alliance_ids.append(0)
    has_more_pages = True
    url = f"https://api.politicsandwar.com/graphql?api_key={helpers.apikey(owner='hughes')}"
    page = 1
    while has_more_pages:
        query = """query{
            nations(first:100, min_score:375, vmode:false, page:%s, alliance_id: %s) {
                paginatorInfo {hasMorePages,lastPage}
                data {id
                defensive_wars {id, turnsleft,war_type,winner
                    attacks {type,loot_info, date, victor}
                    defender {id,alliance_id,score,beigeturns, defensive_wars{turnsleft}}
                    attacker {id, alliance_id, score, beigeturns, defensive_wars{turnsleft}}
                }}}}""" % (str(page), str(alliance_ids))
        success = False
        while not success:
            try:
                data = requests.post(url,json={'query':query}).json()
                data = data['data']['nations']
            except Exception as e:
                print(f"Error: {data}")
                print([key for key in data])
                try:
                    print([key for key in data['data']])
                except:
                    pass
                print(e)
                time.sleep(5)
            else:
                success = True
        has_more_pages = data['paginatorInfo']['hasMorePages']
        nations = data['data']
        for nation in nations:
            check_nation(nation)
        page += 1
    


if __name__ == "__main__":
    with open("raidfinder.txt", 'w') as f:
        f.write("disallow")
    time.sleep(60)
    global prices
    prices = {
        'coal': 3000,
        'oil': 3000,
        'uranium': 3000,
        'iron': 3000,
        'bauxite': 3000,
        'lead': 3000,
        'gasoline': 4000,
        'munitions': 2000,
        'steel': 4000,
        'aluminum': 4000,
        'food': 120
    }
    delete_raid_table = "DROP TABLE IF EXISTS raids"
    create_raid_table = """
        CREATE TABLE IF NOT EXISTS raids (
            nation_id INTEGER,
            score REAL,
            beige_turns INTEGER,
            war_type TEXT,
            open_slots INTEGER,
            alliance_id INTEGER,
            date_looted TEXT,
            nation_loot_raw TEXT,
            nation_loot_value INTEGER,
            bank_loot_raw TEXT,
            bank_loot_value INTEGER,
            total_loot_value INTEGER
        )
    """
    helpers.execute_query(delete_raid_table)
    helpers.execute_query(create_raid_table)
    get_wars()
    data = {}
    data['content'] = "raidfinder updating complete"
    with open("raidfinder.txt", 'w') as f:
        f.write("allow")





def nations_query():
    alliance_ids = []
    ####
    has_more_pages = True
    url = f"https://api.politicsandwar.com/graphql?api_key={helpers.apikey(owner='hughes')}"
    page = 1
    while has_more_pages:
        query = """query{
            nations(first:500, min_score:375, vmode:false, page:%s, alliance_id: %s) {
                paginatorInfo {hasMorePages,lastPage}
                data {id,alliance_id,score,beigeturns
                defensive_wars {id, turnsleft,war_type
                    attacks {type,loot_info, date, victor}
                    defender {id,alliance_id,score,beigeturns}
                }}}}""" % (str(page), str(alliance_ids))
        data = requests.post(url,json={'query':query}).json()['data']['nations']
        has_more_pages = data['paginatorInfo']['hasMorePages']
        nations = data['data']
        for nation in nations:
            check_nation(nation)
        
        # if alliance_id > 0:
            # value += bank_loot
        page += 1

def wars_query():
    url = ""
    ###
    query = """
        query{
            wars(days_ago: 14, active: false, alliance_id:790) {
                id
                turnsleft
                war_type
                winner
                attacks {
                    type
                    loot_info
                    date
                    victor
                }
                defender {
                    id
                    alliance_id
                    score
                    beigeturns
                }
                attacker {
                    id
                    alliance_id
                    score
                    beigeturns
                }
            }
        }
    """
    data = requests.post(url,json={'query':query}).json()['data']['wars']
