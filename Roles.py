from functools import wraps
from flask import g, jsonify

def login_required(f):
    """Ensures a valid session exists before allowing access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(g, 'user_id', None):
            return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_roles(*allowed_roles):
    """
    Checks if the authenticated user has one of the permitted roles.
    Must be placed AFTER @login_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Local import prevents circular dependency issues with app.py
            from DataBase import DataBase 
            
            db = DataBase.get_instance()
            user = db.FindUser(g.user_id)
            
            # If user doesn't exist in DB or lacks required role
            if not user or user.role not in allowed_roles:
                from SecurityLogger import SecurityLogger
                from flask import request
                SecurityLogger.get_instance().log_event(
                    event_type="UNAUTHORIZED_ROLE_ACCESS",
                    user_id=g.user_id,
                    details={"path": request.path, "required": allowed_roles},
                    severity="CRITICAL"
                )
                return jsonify({"status": "error", "message": "Forbidden. Insufficient privileges."}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator