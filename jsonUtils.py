import json
import os
# Helper to read/write your JSON "Database"
def read_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Ensure we only keep actual dictionaries to avoid KeyErrors later
                return [u for u in data if isinstance(u, dict)]
        except (json.JSONDecodeError, ValueError):
            return []
        return []

def write_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
