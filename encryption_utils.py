import os
import json
from cryptography.fernet import Fernet

#data-at-rest encryption
class EncryptedStorage:
    def __init__(self, key_file='secret.key'):
        # Load or generate encryption key
        try:
            with open(key_file, 'rb') as f:
                self.key = f.read()
        except FileNotFoundError:
            self.key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)
    
    def save_encrypted(self, filename, data):
        """Save encrypted JSON data"""
        json_data = json.dumps(data)
        encrypted = self.cipher.encrypt(json_data.encode())
        
        with open(filename, 'wb') as f:
            f.write(encrypted)

    def load_encrypted(self, filename):
        """Load encrypted JSON data"""
        with open(filename, 'rb') as f:
            encrypted = f.read()
            decrypted = self.cipher.decrypt(encrypted)
            return json.loads(decrypted.decode())


# 🛡️ Access the Singleton-safe storage instance
# Note: In a real app, you'd define 'storage' once here or inside app.py
storage = EncryptedStorage()

if __name__ == "__main__":
    # ⚠️ CRITICAL: Any code here ONLY runs if you run this script DIRECTLY.
    # It will NOT run when you import this into app.py or authentication.py.
    
    # 1. Create a safe test file (DON'T overwrite your real users.json!)
    test_file = 'data/test_encryption.json'
    test_data = {"message": "Encryption is working securely!", "status": "verified"}

    print(f"--- 🔒 Encryption Test ---")
    
    # 2. Save encrypted
    storage.save_encrypted(test_file, test_data)
    print(f"Saved encrypted data to: {test_file}")

    # 3. Load and decrypt
    loaded_data = storage.load_encrypted(test_file)
    print(f"Decrypted data: {loaded_data}")
    
    if loaded_data == test_data:
        print("✅ SUCCESS: Data matched perfectly after decryption.")
    else:
        print("❌ ERROR: Decrypted data does not match original.")
