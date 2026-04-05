import json
from encryption_utils import storage

# Paths to your encrypted databases
files_to_check = [
    'data/documents.json',
    'data/sessions.json',
    'data/users.json'
]

for file_path in files_to_check:
    print(f"\n==========================================")
    print(f" Checking: {file_path}")
    print(f"==========================================")
    
    try:
        # Use your existing storage singleton to load and decrypt
        decrypted_data = storage.load_encrypted(file_path)
        
        print("--- DECRYPTED CONTENTS ---")
        # Print the result cleanly formatted
        print(json.dumps(decrypted_data, indent=4))
        print("--------------------------\n")
        
    except FileNotFoundError:
        print(f"❌ Error: The file {file_path} does not exist. (It might not be created yet)")
    except Exception as e:
        print(f"❌ Failed to decrypt {file_path}.")
        print(f"   Are you sure it's encrypted? Error: {e}\n")