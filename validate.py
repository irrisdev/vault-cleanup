import json


with open('data/clean.json') as f:
    finished_entries = json.load(f)

filtered_entries = [entry for entry in finished_entries if entry.get('type') == 1]

print(json.dumps(filtered_entries,indent=4))