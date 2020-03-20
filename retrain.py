import json, os

with open("./data.json", "r") as f:
    botJson = json.load(f)
    botJson["last_id"] = 1
    botJson["done"] = []
with open("./data.json", "w") as f:
    json.dump(botJson, f, indent=4, sort_keys=True)

os.remove("./markov.json")
