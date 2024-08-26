from dotenv import load_dotenv
import requests
import json
import os
import hashlib

# Load environment variables from .env file
load_dotenv()

# Function to hash a given value using SHA-256
def hasher(value):
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()

class APIClient:
    def __init__(self):
        self.BASE_URL = os.getenv("URL") 

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
                if key in hash_key_values and value is not None:
                    data[key] = hasher(value) 
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

def create_entries(data):
    """Create new entries by extracting and mapping fields from the data."""
    new_entries = []
    
    for item in data:
        new_entry = {}
        
        for new_key, path in fields_to_extract.items():
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

# List of keys that should be hashed
hash_key_values = ['password', 'passwordHistory', 'fido2Credentials', 'totp']

# Fields to extract and their corresponding paths in the original data
fields_to_extract = {
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

# Initialize the API client
client = APIClient()

# Fetch and process items
final = create_entries(client.get_items(folderid="d171e53f-01e3-4a92-bcdc-b1af014d39c0") )

# Save the final output to a JSON file
with open('data/clean.json', 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=4)
