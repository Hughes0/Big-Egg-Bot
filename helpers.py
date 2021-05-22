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