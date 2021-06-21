import json
import random
import requests
import sqlite3
from sqlite3 import Error
import datetime


def get_data():
    with open("keys.json") as f:
        data = json.loads(f.read())
    return data


def login(session):
    login_url = "https://politicsandwar.com/login/"
    data = get_data()
    login_data = {
        "email": data['email'],
        "password": data['password'],
        "loginform": "Login"
    }
    session.post(url=login_url, data=login_data)


def execute_query(filename, query, arguments=None):
    # execute a write query on a database
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()
    try:
        if not arguments:
            cursor.execute(query)
        else:
            cursor.execute(query, arguments)
        connection.commit()
        print(f"{datetime.datetime.now()}: Executed write query to {filename} successfully")
    except Error as e:
        raise Exception(e)


def read_query(filename, query, arguments=None):
    # execute a read query on a database
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()
    try:
        if not arguments:
            cursor.execute(query)
        else:
            cursor.execute(query, arguments)
        result = cursor.fetchall()
        print(f"{datetime.datetime.now()}: Read from database in {filename} successfully")
        return result
    except Error as e:
        raise Exception(e)


def apikey(alliance_id=None, requests_needed=1, bank_access=False, owner=None):
    query = f"SELECT * FROM keys WHERE requests_remaining >= {requests_needed}"
    if alliance_id:
        query += f" AND alliance_id = {alliance_id}"
    if bank_access:
        query += f" AND alliance_position >= 4"
    if owner:
        query += f" AND owner = '{owner}'"
    results = read_query('databases/keys.sqlite', query)
    if not bank_access:
        non_bank_keys = []
        for entry in results:
            if entry[3] < 4 and entry[4] >= requests_needed:
                non_bank_keys.append(entry)
        if non_bank_keys:
            return random.choice(non_bank_keys)[0]
    return random.choice(results)[0]


def check(ctx, level):
    # 10: bot admin
    # 9: eclipse leaders
    # 8: eclipse bankaccess
    # 7: all highgov
    # 6: all lowgov
    # 5: 
    # 4: 
    # 3: 
    # 2: all members
    # 1: basic
    # roles of user requesting to use command
    roles = [role.id for role in ctx.author.roles]
    # ids of roles with allowed permissions
    query = f"SELECT role_id FROM permissions WHERE permission_level >= {level}"
    allowed_roles = [entry[0] for entry in read_query('databases/permissions.sqlite', query)]
    for role in roles:
        if role in allowed_roles:
            return True
    return False
    # raise Exception("Missing permissions")


def perms_ten(ctx):
    return check(ctx, 10)

def perms_nine(ctx):
    return check(ctx, 9)

def perms_eight(ctx):
    return check(ctx, 8)

def perms_seven(ctx):
    return check(ctx, 7)

def perms_six(ctx):
    return check(ctx, 6)

def perms_five(ctx):
    return check(ctx, 5)

def perms_four(ctx):
    return check(ctx, 4)

def perms_three(ctx):
    return check(ctx, 3)

def perms_two(ctx):
    return check(ctx, 2)

def perms_one(ctx):
    return check(ctx, 1)

def has_account(ctx):
    # allow level 10 OR people with an account in account.sqlite
    result = [entry[0] for entry in read_query('databases/accounts.sqlite', "SELECT owner_discord_id FROM accounts")]
    if perms_ten(ctx) or ctx.author.id in result:
        return True
    else:
        return False





def check_city_inputs(min_cities, max_cities):
    # function to make sure min and max city inputs are valid
    try:
        min_cities = int(max_cities)
        max_cities = int(max_cities)
    except:
        raise ValueError("Invalid input")
    if min_cities > max_cities:
        raise ValueError("min_cities must be greater than max_cities")
    if min_cities < 0 or max_cities < 0 or min_cities > 100 or max_cities > 100:
        raise ValueError("Inputs out of range")


def catch_api_error(data, version):
    if version == 1:
        keys = [key for key in data]
        if 'error' in keys:
            raise Exception(data['error'])
        if 'general_message' in keys:
            raise Exception(data['general_message'])
    elif version == 2:
        if not data['api_request']['success']:
            raise Exception(data['api_request']['error_msg'])
    elif version == 3:
        pass
    else:
        raise ValueError("Invalid API version for catch_api_error()")


def prices(resources):
    _apikey = apikey()
    if resources == "all":
        resources = ["food", "coal", "oil", "uranium", "lead", "iron", "bauxite", "gasoline", "munitions", "steel", "aluminum"]
    prices_dict = {}
    for resource in resources:
        url = f"https://politicsandwar.com/api/tradeprice/?resource={resource.lower()}&key={_apikey}"
        data = requests.get(url).json()
        catch_api_error(data, version=1)
        prices_dict[resource] = data
    return prices_dict


def cached_prices():
    query = "SELECT * FROM prices"
    result = read_query('databases/game_data.sqlite', query)
    price_data = {}
    for entry in result:
        price_data[entry[0]] = {
            "sell_market": entry[1],
            "buy_market": entry[2],
            "avg_price": entry[3]
        }
    return price_data


def get_arguments(args):
    parsed = {}
    for arg in args:
        arg = arg.split("=")
        parsed[arg[0]] = arg[1]
    return parsed


def api_v2_dom_policy(code_num):
    mapping = [
        "Manifest Destiny",
        "Open Markets",
        "Technological Advancement",
        "Imperialism",
        "Urbanization"
    ]
    return mapping[code_num - 1]


def api_v2_war_policy(code_num):
    mapping = [
        "Attrition",
        "Turtle",
        "Blitzkrieg",
        "Fortress",
        "Moneybags",
        "Pirate",
        "Tactician",
        "Guardian",
        "Covert",
        "Arcane"
    ]
    return mapping[code_num - 1]


def spies(nation_id, war_policy):
    safety_level = 2
    att_spies = 60
    while att_spies > 0:
        odds = requests.get(f"https://politicsandwar.com/war/espionage_get_odds.php?id1=1&id2={nation_id}&id3=6&id4={safety_level}&id5={att_spies}").text.split(" ")[0].lower()
        if odds == "lower": break
        att_spies -= 1
    if war_policy.lower() == "tactician":
        odds = 43.5
    elif war_policy.lower() == "arcane":
        odds = 55.5
    else:
        odds = 50
    def_spies = int(round((((100*(att_spies+1))/((odds*1.5)-(25*safety_level)))-1)/3,0))
    if def_spies > 60:
        def_spies = 60
    elif def_spies <= 1:
        def_spies = 0
    return def_spies


def rss_list_to_dict(resources):
    resources_dict = {}
    for i in range(0, len(resources), 2):
        resources_dict[resources[i+1]] = float(resources[i])
    for resource in ["cash", "food", "coal", "oil", "uranium", "lead", "iron", "bauxite", "gasoline", "munitions", "steel", "aluminum"]:
        if resource not in resources_dict:
            resources_dict[resource] = 0
    return resources_dict


def parse_keyword_args(args):
    args_dict = {}
    for arg in args:
        if '=' not in arg:
            raise Exception("Invalid input")
        key_value = arg.split('=')
        try:
            value = int(value.replace(',', ''))
            try:
                value = float(value.replace(',', ''))
            except:
                value = key_value[1]
        except:
            value = key_value[1]
        args_dict[key_value[0]] = value
    return args_dict



def alliance_id_to_name():
    url = f"https://politicsandwar.com/api/alliances/?key={apikey()}"
    response = requests.get(url).json()
    alliances = response['alliances']
    lookup_dict = {}
    for alliance in alliances:
        lookup_dict[str(alliance['id'])] = alliance['name']
    return lookup_dict


def paginate_list(array, per_chunk):
    return [array[i:i+per_chunk] for i in range(0, len(array), per_chunk)]