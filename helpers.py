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


def apikey(alliance_id=None, requests_needed=1, bank_access=False):
    # get apikey from keys.json that matches the requested criteria
    with open("keys.json") as f:
        apikeys = json.loads(f.read())['apikeys']
    if bank_access:
        min_alliance_position = 4
    else:
        min_alliance_position = 0
    apikey_options = [key for key in apikeys 
                            if apikeys[key]['alliance_position'] >= min_alliance_position
                            and apikeys[key]['requests_remaining'] >= requests_needed]
    if alliance_id:
        apikey_options = [key for key in apikey_options if apikeys[key]['alliance_id'] == alliance_id]
    if not apikey_options:
        raise Exception("No valid API key found")
    return apikeys[random.choice(apikey_options)]


def update_apikey(owner):
    # update an apikey's info in keys.json
    with open("keys.json") as f:
        content = json.loads(f.read())
        apikeys = content['apikeys']
    try:
        entry = apikeys[owner]
    except:
        raise Exception(f"API key for {owner} not found")
    url = f"https://politicsandwar.com/api/v2/nations/{entry['key']}/&alliance_id=0&min_score=3000"
    data = requests.get(url).json()['api_request']['api_key_details']
    new_entry = {
        "key": entry['key'],
        "alliance_id": data['alliance_id'],
        "alliance_position": data['alliance_position'],
        "requests_remaining": data['daily_requests_remaining']
    }
    content["apikeys"][owner] = new_entry
    with open("keys.json", 'w') as f:
        json.dump(content, f, indent=4)




def execute_query(filename, query):
    # execute a write query on a database
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print(f"{datetime.datetime.now()}: Executed write query to {filename} successfully")
    except Error as e:
        raise Exception(e)


def read_query(filename, query):
    # execute a read query on a database
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        print(f"{datetime.datetime.now()}: Read from database in {filename} successfully")
        return result
    except Error as e:
        raise Exception(e)


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
    raise Exception("Missing permissions")


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