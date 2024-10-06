import hashlib
import os
import sys
import requests
import concurrent.futures

class APIClient:
    def __init__(self):
        self.BASE_URL = os.getenv("URL", "http://localhost:8087")
        self.hash_key_values = ['password', 'passwordHistory', 'fido2Credentials', 'totp']
        self.fields_to_extract = {
        'id': 'id',
        'name': 'name',
        'username': 'login.username',
        'password': 'login.password',
        'revisionDate': 'revisionDate',
        'creationDate': 'creationDate',
        'deletedDate': 'deletedDate',
        'uri': 'login.uris.uri',
        'totp': 'login.totp',
        'type':'type'
        }

    def _hasher(self, value):
        return hashlib.sha256(str(value).encode('utf-8')).hexdigest()

    def _make_request(self, endpoint, method='GET', params=None, json=None):
        """Make an HTTP request and return the JSON response."""
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = requests.request(method, url, params=params, json=json)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def _hash_values(self, data):
        """Recursively hash sensitive values in a dictionary or list."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key in self.hash_key_values and value is not None:
                    data[key] = self._hasher(value) 
                else:
                    self._hash_values(value)
        elif isinstance(data, list):
            for element in data:
                self._hash_values(element)

    def _filter_json(self, data):
        """Filter and process the JSON data received from the API."""
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
            if isinstance(data, dict) and data.get('object') == "list":
                data = data.get('data', [])

            self._hash_values(data)
            return [item for item in data if item.get("type") == 1]
        return []

    def get_folders(self):
        """Retrieve a list of folders."""
        return self._make_request("/list/object/folders")

    def get_items(self, folderid=None, search=None):
        """Retrieve items, optionally filtered by folder ID or search term."""
        params = {}
        if folderid is not None:
            params['folderid'] = folderid
        if search is not None:
            params['search'] = search
        return self._filter_json(self._make_request("/list/object/items", params=params))

    def get_item(self, item_id):
        """Retrieve a specific item by its ID."""
        return self._filter_json(self._make_request(f"/object/item/{item_id}"))
    
    def prompt_user_confirmation(self, message):
        user_input = input(f"{message} (y/n): ").strip().lower()
        return user_input in {'y', 'yes'}

    def delete_item(self, item_id):
        response = self._make_request(f'/object/item/{item_id}', method='DELETE')
        if response['success']:
            return {'item_id': item_id,"success": True}
        else:
            {'item_id': item_id, 'success': False}

    def delete_items(self, removed):
        
        if not self.prompt_user_confirmation("Proceed to delete these duplicate items?"):
            print("Operation canceled.")
            return {
                'success_count': 0,
                'failure_count': 0,
                'failed_items': []
            }

        success_count = 0
        failure_count = 0
        failed_items = []

        def delete_task(item_id):
            result = self.delete_item(item_id)
            return result
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Create a future-to-item_id mapping
            future_to_id = {executor.submit(delete_task, item['id']): item['id'] for item in removed if item.get('id')}

            for future in concurrent.futures.as_completed(future_to_id):
                result = future.result()
                item_id = result['item_id']
                if result['success']:
                    success_count += 1
                    print(f'Item Deletion {success_count}: {item_id} successfully deleted\n')
                else:
                    failure_count += 1
                    failed_items.append(item_id)

        print(f"Deletion Summary: {success_count} items successfully deleted.")
        if failure_count > 0:
            print(f"{failure_count} deletions failed. Failed items: {failed_items}\n")
        else:
            print("All deletions were successful.\n")

        return {
            'success_count': success_count,
            'failure_count': failure_count,
            'failed_items': failed_items
        }
    
    def create_entries(self, data):
        """Create new entries by extracting and mapping fields from the data."""
        new_entries = []
        
        for item in data:
            new_entry = {}
            
            for new_key, path in self.fields_to_extract.items():
                keys = path.split('.')
                
                value = item
                for key in keys:
                    if isinstance(value, list):
                        if key == 'uri':
                            value = value[0].get('uri') if len(value) > 0 else None
                        else:
                            value = value[0] if len(value) > 0 else None
                    else:
                        value = value.get(key)
                    
                    if value is None:
                        break
                    
                if (new_key == 'username' or new_key == 'uri') and isinstance(value, str):
                    value = value.lower()
                
                new_entry[new_key] = value
            
            new_entries.append(new_entry)
        
        return new_entries

class DataCleaner:
    def __init__(self):
        self.entries = []

    def load_entries(self, data):
        self.entries = data

    def process_dupes(self):
        """Process and clean entries to remove duplicates."""
        from collections import defaultdict
        from datetime import datetime

        initial_count = len(self.entries)
        grouped_entries = defaultdict(list)
        
        for entry in self.entries:
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
        count_totp, count_no_totp = 0, 0

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

        # Store the cleaned and deleted entries in memory
      
        self.deleted_entries = deleted_entries
        self.cleaned_entries = unique_entries

        print(f"\nTotal Vault Items: {initial_count}")
        print(f"Number of unique items: {len(unique_entries)}")
        # print(f"Number of entries with TOTP: {count_totp}")
        # print(f"Number of entries without TOTP: {count_no_totp}")
        print(f"Number of duplicate items: {len(deleted_entries)}\n")

        if len(deleted_entries)<1:
            print("No duplicates found, Terminating Program")
            sys.exit()

    def get_cleaned_entries(self):
        return self.cleaned_entries

    def get_deleted_entries(self):
        return self.deleted_entries

class Validator:
    def __init__(self):
        self.cleaned_entries = []
        self.deleted_entries = []

    def load_cleaned_entries(self, data):
        self.cleaned_entries = data

    def load_deleted_entries(self, data):
        self.deleted_entries = data

    def filter_by_type(self, entry_type):
        filtered_entries = [entry for entry in self.cleaned_entries if entry.get('type') == entry_type]
        return filtered_entries

    def validate_deleted_entries(self):
        """Validate that every deleted entry has a matching record in the cleaned entries."""
        missing_records = []

        # Create a set of (uri, username) pairs from cleaned entries
        cleaned_lookup = {(entry['uri'], entry['username']) for entry in self.cleaned_entries}

        # Check each deleted entry
        for entry in self.deleted_entries:
            uri_username_pair = (entry['uri'], entry['username'])
            if uri_username_pair not in cleaned_lookup:
                missing_records.append(entry)

        if missing_records:
            print("Some deleted entries do not have a match in cleaned entries:")
            for record in missing_records:
                print(record)
        else:
            print("All deleted entries have matching records in the cleaned entries.")


if __name__ == "__main__":

    # set environment variables
    os.environ["URL"] = "http://localhost:8087"

    # Initialize the classes
    client = APIClient()
    cleaner = DataCleaner()
    validator = Validator()

    api_data = client.get_items() 
    entries = client.create_entries(api_data)

    cleaner.load_entries(entries)
    cleaner.process_dupes()

    validator.load_cleaned_entries(cleaner.cleaned_entries)
    validator.load_deleted_entries(cleaner.deleted_entries)
    
    validator.validate_deleted_entries()
    
    client.delete_items(cleaner.deleted_entries)
