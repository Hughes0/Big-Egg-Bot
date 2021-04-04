import json
import random
import requests
import sys


def get_data():
    with open("keys.json") as f:
        data = json.loads(f.read())
    return data


def apikey(alliance_id=None, requests_needed=1, bank_access=False):
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
    return apikeys[random.choice(apikey_options)]


def update_apikey(owner):
    with open("keys.json") as f:
        content = json.loads(f.read())
        apikeys = content['apikeys']
    entry = apikeys[owner]
    url = f"https://politicsandwar.com/api/v2/nations/{entry['key']}//&alliance_id=0&min_score=3000"
    data = requests.get(url).json()['api_request']['api_key_details']
    print(data)
    new_entry = {
        "key": entry['key'],
        "alliance_id": data['alliance_id'],
        "alliance_position": data['alliance_position'],
        "requests_remaining": data['daily_requests_remaining']
    }
    content["apikeys"][owner] = new_entry
    print(content)
    with open("keys.json", 'w') as f:
        json.dump(content, f, indent=4)