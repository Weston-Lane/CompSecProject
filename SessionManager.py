import json
import os
import secrets
import time
from flask import request, g, make_response, redirect

class SessionManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        """Global access point for the Session Manager."""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self, timeout=1800):
        self.timeout = timeout
        self.absolute_timeout = 43200 
        self.sessions_file = 'data/sessions.json'
        # Load sessions into memory exactly once upon server start
        self.sessions = self._load_sessions()

    def _load_sessions(self) -> dict:
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, ValueError):
                return {}
        return {}

    def _save_sessions(self):
        """Internal helper to sync memory to disk."""
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=4)

    # --- Public Methods ---

    def create_session(self, user_id: str) -> str:
        # 1. NEW: Find and destroy any existing sessions for this user
        # We collect the keys in a list first to avoid modifying a dictionary while looping over it
        stale_tokens = [
            token for token, session_data in self.sessions.items() 
            if session_data['user_id'] == user_id
        ]
        
        for stale_token in stale_tokens:
            del self.sessions[stale_token]
        """Creates a new session, saves to disk, and returns the secure token."""
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_activity': time.time(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }
        
        # Save to disk only when a new user logs in
        self._save_sessions() 
        return token

    def validate_session(self, token: str) -> dict | None:
        """Validates a token against memory (lightning fast)."""
        session = self.sessions.get(token)
        
        if not session:
            return None

        # Check for timeout
        if time.time() - session['last_activity'] > self.timeout:
            self.destroy_session(token)
            return None
        
        #if 12hr session delete session
        if time.time() - session['created_at'] > self.absolute_timeout:
            self.destroy_session(token)
            return None

        # Update last activity in MEMORY ONLY to avoid disk I/O on every page load
        session['last_activity'] = time.time()
        return session

    def destroy_session(self, token: str):
        """Removes the session and syncs the deletion to disk."""
        if token in self.sessions:
            del self.sessions[token]
            
            # Save to disk only when a user logs out or times out
            self._save_sessions()
