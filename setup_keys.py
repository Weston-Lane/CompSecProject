import os
import secrets
from cryptography.fernet import Fernet # Assuming you use Fernet in encryption_utils

def generate_env_file():
    env_file = '.env'
    
    # Generate secure keys
    flask_secret = secrets.token_hex(32)
    fernet_key = Fernet.generate_key().decode('utf-8')
    
    # Write them to the .env file
    with open(env_file, 'w') as f:
        f.write(f"FLASK_SECRET_KEY={flask_secret}\n")
        f.write(f"ENCRYPTION_KEY={fernet_key}\n")
        
    print(f" Fresh keys have been generated and saved to {env_file}")
    print("You may now start the application.")

if __name__ == "__main__":
    generate_env_file()