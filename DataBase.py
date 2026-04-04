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
            # FALLBACK: Try to load as PLAIN JSON for data migration
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

####################################Document Managment###########################
# --- Document Management Methods ---

    def SaveDocuments(self):
        """Saves the document metadata list to disk using encryption."""
        #storage.save_encrypted(self.documentsFilePath, self.documents)
        jsonUtils.write_json(self.documentsFilePath, self.documents)

    def AddDocument(self, doc_id: str, original_filename: str, content_type: str, owner_id: str):
        """Adds a new document record to memory and saves it."""
        import time
        doc_record = {
            "file_id": doc_id,
            "original_filename": original_filename,
            "content_type": content_type,
            "owner_id": owner_id,
            "shared_with": [], # Initialize empty list for sharing
            "upload_time": time.time()
        }
        self.documents.append(doc_record)
        self.SaveDocuments()

    def GetDocument(self, file_id: str) -> dict | None:
        """Retrieves a single document's metadata by its ID."""
        for doc in self.documents:
            if doc.get('file_id') == file_id:
                return doc
        return None

    def GetUserDocuments(self, username: str) -> list:
        """Returns a list of all documents owned by a specific user."""
        return [doc for doc in self.documents if doc.get('owner_id') == username]

    def GetSharedDocuments(self, username: str) -> list:
        """Returns a list of documents that have been shared with a specific user."""
        return [doc for doc in self.documents if username in doc.get('shared_with', [])]

    def ShareDocument(self, file_id: str, owner_username: str, target_username: str) -> bool:
        """
        Grants access to a document to another user.
        Validates that the requesting user is the actual owner.
        """
        for doc in self.documents:
            if doc.get('file_id') == file_id:
                # Security constraint: Only the owner can share the file
                if doc.get('owner_id') != owner_username:
                    return False
                
                # Prevent duplicate shares
                if target_username not in doc.get('shared_with', []):
                    # Ensure the list exists, then append
                    if 'shared_with' not in doc:
                        doc['shared_with'] = []
                    doc['shared_with'].append(target_username)
                    self.SaveDocuments()
                return True
        return False
    
    def DeleteDocument(self, file_id: str, requesting_user: str) -> str:
        """
        Handles document deletion logic based on user role.
        - If owner: Deletes the document metadata entirely. Returns "DELETED_ALL".
        - If shared user: Removes the user from the shared_with list. Returns "REMOVED_SHARE".
        - Otherwise: Returns "UNAUTHORIZED" or "NOT_FOUND".
        """
        for i, doc in enumerate(self.documents):
            if doc.get('file_id') == file_id:
                
                # Case 1: The user is the absolute owner
                if doc.get('owner_id') == requesting_user:
                    del self.documents[i]
                    self.SaveDocuments()
                    return "DELETED_ALL"
                
                # Case 2: The user is in the shared_with list
                elif requesting_user in doc.get('shared_with', []):
                    doc['shared_with'].remove(requesting_user)
                    self.SaveDocuments()
                    return "REMOVED_SHARE"
                
                # Case 3: The user has no rights to this file whatsoever
                else:
                    return "UNAUTHORIZED"
                    
        return "NOT_FOUND"
    
            
    
    def ClearAllDocuments(self, wipe_physical_files=True):
            """
            Removes all document metadata from memory and disk.
            If wipe_physical_files is True, it also deletes the encrypted binaries in the uploads folder.
            """
            import os
            import shutil

            # 1. Wipe the physical files if requested
            if wipe_physical_files:
                upload_dir = 'uploads'
                if os.path.exists(upload_dir):
                    # Delete the entire folder and its contents
                    shutil.rmtree(upload_dir)
                    # Recreate the empty folder so future uploads don't crash
                    os.makedirs(upload_dir, exist_ok=True)

    def ClearUsers(self):
        self.users.clear()
        self.SaveUsers()