import json
import os
# Helper to read/write your JSON "Database"
def read_json(filename):
    path = f'data/{filename}.json'
    if not os.path.exists(path):
        return [] # Return empty list if file doesn't exist yet
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return [] # Return empty list if file is empty/corrupt

def write_json(filename, data):
    with open(f'data/{filename}.json', 'w') as f:
        json.dump(data, f, indent=4)