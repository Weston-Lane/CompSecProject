import logging
import json
import os
from datetime import datetime, timezone
from flask import request, has_request_context

class SecurityLogger:
    _instance = None

    @classmethod
    def get_instance(cls):
        """Global access point for the Security Logger."""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self, log_file='data/logs/security.log'):
        # 1. Prevent FileNotFoundError by ensuring the directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # 2. Prevent duplicate logs by checking if handlers already exist
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            # Output pure JSON instead of mixing text prefixes with JSON bodies
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event(self, event_type: str, user_id: str = None, details: dict = None, severity: str = 'INFO'):
        """Logs a structured security event in JSON format."""
        
        # 3. Context Safety: Prevent crashes if called outside a Flask route (e.g., startup scripts)
        ip_addr = request.remote_addr if has_request_context() else 'SYSTEM'
        user_agent = request.headers.get('User-Agent') if has_request_context() else 'SYSTEM'
        
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'severity': severity.upper(),
            'event_type': event_type.upper(),
            'user_id': user_id or 'ANONYMOUS',
            'ip_address': ip_addr,
            'user_agent': user_agent,
            'details': details or {}
        }
        
        json_msg = json.dumps(log_entry)
        
        # Route to the correct logging level
        level = severity.upper()
        if level == 'CRITICAL':
            self.logger.critical(json_msg)
        elif level == 'ERROR':
            self.logger.error(json_msg)
        elif level == 'WARNING':
            self.logger.warning(json_msg)
        else:
            self.logger.info(json_msg)