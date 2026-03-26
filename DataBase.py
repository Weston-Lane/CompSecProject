import jsonUtils
from User import User
#DataBase is a singleton
class Database:
    _instance = None

    def __init__(self):
        # We raise an error to prevent people from accidentally calling Database()
        if Database._instance is not None:
            raise Exception("This class is a singleton! Use Database.get_instance() instead.")

    @classmethod
    def get_instance(cls):
        """The explicit global access point."""
        if cls._instance is None:
            # Create the one and only instance
            cls._instance = cls.__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Runs only once when the first instance is created."""
        self.usersFilePath = 'data/users.json'
        self.documentsFilePath = 'data/documents.json'
        self.accessLogPath = 'data/logs/access.log'
        self.securityLogPath = 'data/logs/security.log'
        
        # Keep data in memory
        self.users = self._load(self.usersFilePath)
        self.documents = self._load(self.documentsFilePath)
        self.accessLog = self._load(self.accessLogPath)
        self.securityLog = self._load(self.securityLogPath)

    def _load(self, path):
        return jsonUtils.read_json(path)

    def SaveUsers(self):
        jsonUtils.write_json(self.usersFilePath, self.users)
    
    def AddUser(self, user):
        userDict = user.AsDict()
        self.users.append(userDict)

    def FindUser(self, username):
        for userDict in self.users:
            if userDict.get('username') == username:
                return User(**userDict)
        return None

