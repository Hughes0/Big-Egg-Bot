import json


def get_entry(key):
    with open("keys.json") as f:
        data = json.loads(f.read())
    return data[key]