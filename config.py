import json

def config_get(key):
    with open('config.json', 'r') as fp:
        return json.load(fp)[key]
