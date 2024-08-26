from collections import defaultdict
from datetime import datetime
import json

def process_entries(input_file, finished_file, deleted_file):

    with open(input_file) as f:
        entries = json.load(f)

    initial_count = len(entries)

    grouped_entries = defaultdict(list)
    for entry in entries:
        key = (entry['uri'], entry['username'], entry['password'])
        grouped_entries[key].append(entry)

    def select_best_entry(entries):
        entries.sort(key=lambda x: (
            datetime.fromisoformat(x['revisionDate'].replace('Z', '+00:00')),
            datetime.fromisoformat(x['creationDate'].replace('Z', '+00:00')),
            x.get('totp') is not None
        ), reverse=True)
        
        return entries[0]

    unique_entries = []
    deleted_entries = []

    count_totp = 0
    count_no_totp = 0

    for group in grouped_entries.values():
        best_entry = select_best_entry(group)
        unique_entries.append(best_entry)
        
        for entry in group:
            if entry != best_entry:
                deleted_entries.append(entry)
            
            if entry.get('totp') is not None:
                count_totp += 1
            else:
                count_no_totp += 1

    with open(finished_file, 'w') as file:
        json.dump(unique_entries, file, indent=4)

    with open(deleted_file, 'w') as file:
        json.dump(deleted_entries, file, indent=4)

    # Print statistics
    print(f"Initial number of entries: {initial_count}")
    print(f"Number of unique entries: {len(unique_entries)}")
    print(f"Number of entries with totp: {count_totp}")
    print(f"Number of entries without totp: {count_no_totp}")
    print(f"Number of entries sent to deleted file: {len(deleted_entries)}")

# Usage
process_entries('data/clean.json', 'data/finished.json', 'data/deleted.json')
