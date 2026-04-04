import os
import jsonUtils
from User import User
from encryption_utils import storage # Use the global storage instance we set up

# DataBase is a singleton
class DataBase:
    _instance = None

    def __init__(self):
        # Prevent manual instantiation
        if DataBase._instance is not None:
            raise Exception("This class is a singleton! Use DataBase.get_instance() instead.")

    @classmethod
    def get_instance(cls):
        """Global access point for the database."""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Runs only once when the first instance is created."""
        self.usersFilePath = 'data/users.json'
        self.documentsFilePath = 'data/documents.json'
        
        # Load and automatically handle migration from plain text to encrypted
        self.users = self._secure_load(self.usersFilePath)
        self.documents = self._secure_load(self.documentsFilePath)

    def _secure_load(self, path: str):
        """
        Attempts to load data via decryption. 
        If it fails (likely plain JSON or missing file), handles it gracefully.
        """
        if not os.path.exists(path):
            return []

        try:
            # Attempt: Load as ENCRYPTED
            print(f"---  Loading {path} (Encrypted) ---")
            return storage.load_encrypted(path)
        except Exception as e:
            # FALLBACK: Try to load as PLAIN JSON (Migration path)
            print(f"---  WARNING: Decryption failed for {path} ---")
            print(f"---  Attempting Migration for {path} ---")
            try:
                data = jsonUtils.read_json(path)
                # If we successfully read plain JSON, immediately encrypt it for next time
                storage.save_encrypted(path, data)
                print(f"---  SUCCESS: {path} has been migrated to encrypted format. ---")
                return data
            except Exception as e2:
                # If it's not even valid JSON, return empty list
                print(f"---  ERROR: Could not read {path} as plain JSON either. ---")
                return []

    def SaveUsers(self):
        """Saves the user list to disk using encryption."""
        storage.save_encrypted(self.usersFilePath, self.users)
    
    def AddUser(self, user: User):
        """Adds a user object to memory and immediately saves it encrypted."""
        userDict = user.AsDict()
        self.users.append(userDict)
        self.SaveUsers()

    def FindUser(self, username: str):
        """Standard lookup to find a user by username."""
        for userDict in self.users:
            if userDict.get('username') == username:
                return User(**userDict)
        return None
    
    def UpdateUser(self, updated_user: User):
        """Update a user's record and save the changes."""
        for i, user_dict in enumerate(self.users):
            if user_dict.get('username') == updated_user.username:
                self.users[i] = updated_user.AsDict()
                self.SaveUsers()
                return True
        return False
