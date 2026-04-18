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

    def _initialize(self, sec_file='data/logs/security.log', acc_file='data/logs/access.log'):
        os.makedirs(os.path.dirname(sec_file), exist_ok=True)
        
        # Security Logger
        self.sec_logger = logging.getLogger('security')
        self.sec_logger.setLevel(logging.INFO)
        if not self.sec_logger.handlers:
            h1 = logging.FileHandler(sec_file)
            h1.setFormatter(logging.Formatter('%(message)s'))
            self.sec_logger.addHandler(h1)

        # Access Logger
        self.acc_logger = logging.getLogger('access')
        self.acc_logger.setLevel(logging.INFO)
        if not self.acc_logger.handlers:
            h2 = logging.FileHandler(acc_file)
            h2.setFormatter(logging.Formatter('%(message)s'))
            self.acc_logger.addHandler(h2)

    def log_event(self, event_type: str, user_id: str = None, details: dict = None, severity: str = 'INFO', log_type: str = 'security'):
        ip_addr = request.remote_addr if has_request_context() else 'SYSTEM'
        user_agent = request.headers.get('User-Agent') if has_request_context() else 'SYSTEM'
        
        # Automatically pull user_id from Flask 'g' if not explicitly provided
        from flask import g
        active_user = user_id or (g.user_id if has_request_context() and getattr(g, 'user_id', None) else 'ANONYMOUS')

        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'severity': severity.upper(),
            'event_type': event_type.upper(),
            'user_id': active_user,
            'ip_address': ip_addr,
            'user_agent': user_agent,
            'details': details or {}
        }
        
        json_msg = json.dumps(log_entry)
        target_logger = self.sec_logger if log_type == 'security' else self.acc_logger
        
        level = severity.upper()
        if level == 'CRITICAL':
            target_logger.critical(json_msg)
        elif level == 'ERROR':
            target_logger.error(json_msg)
        elif level == 'WARNING':
            target_logger.warning(json_msg)
        else:
            target_logger.info(json_msg)