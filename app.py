from flask import Flask, request, jsonify, render_template, g, make_response, redirect
from flask_cors import CORS # Allows your frontend to talk to the backend
import bcrypt
import jsonUtils
import authentication
from SecurityLogger import SecurityLogger
from SessionManager import SessionManager
app = Flask(__name__)
CORS(app) # Prevents "Cross-Origin" errors during local development

@app.after_request
def set_security_headers(response):
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; " # Avoid unsafe-inline in production
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'"
    )
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # XSS Protection (legacy, but still useful)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Permissions Policy
    response.headers['Permissions-Policy'] = (
    'geolocation=(), microphone=(), camera=()'
    )
    # HSTS (HTTP Strict Transport Security)
    response.headers['Strict-Transport-Security'] = (
    'max-age=31536000; includeSubDomains'
    )
    return response

@app.before_request
def require_https():
    if not request.is_secure and app.env != "development":
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)
    
@app.before_request
def load_user_session():
    """Checks the session cookie before routing the request."""
    g.user_id = None
    
    # 1. Skip validation for static files
    if request.endpoint == 'static':
        return
    
    # 2. Skip validation for public, unauthenticated routes
    public_routes = ['/api/login', '/api/register', '/', '/register']
    if request.path in public_routes:
        return
    
    # 2. Look for the cookie in the incoming request
    token = request.cookies.get('session_token')
    
    # 3. If a cookie exists, verify it with our Singleton
    if token:
        session_manager = SessionManager.get_instance()
        session_data = session_manager.validate_session(token)
        
        # 4. If the session is still active, attach the username to the global 'g' object
        if session_data:
            g.user_id = session_data['user_id']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def registerUser():
    return authentication.registerUser(request.json)

# This should be a long, random string. Do not expose it in production.
app.config['SECRET_KEY'] = 'super-secret-key-for-project' 

@app.route('/api/login', methods=['POST'])
def login():
    return authentication.LoginUser(request.json)

@app.route('/api/logout', methods=['POST'])
def logout_user():
    # 1. Get the token from the user's cookie
    token = request.cookies.get('session_token')
    
    if token:
        # 2. Destroy the session on the server side
        session_manager = SessionManager.get_instance()
        session_manager.destroy_session(token)
        
        # Optional: Log the logout event
        security_log = SecurityLogger.get_instance()
        security_log.log_event(
            event_type="LOGOUT_SUCCESS",
            user_id=g.user_id if getattr(g, 'user_id', None) else "UNKNOWN",
            details={"message": "User actively logged out."}
        )

    # 3. Create a response to send back to the browser
    response = make_response(jsonify({
        "status": "success", 
        "message": "Successfully logged out"
    }))
    
    # 4. Tell the browser to delete the cookie by setting its expiration to 0
    response.set_cookie(
        'session_token', 
        '', 
        expires=0, 
        httponly=True, 
        secure=True, 
        samesite='Strict'
    )
    
    return response, 200

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/register')
def goToRegisterPage():
    return render_template('register.html')

@app.route('/')
def goToLoginPage():
    return render_template('index.html')



@app.errorhandler(429)
def ratelimit_handler(e):
    ###LOG
    SecurityLogger.log_event(
        event_type='RATE_LIMIT_EXCEEDED',
        user_id=None,  # Typically None during a brute-force attack before login
        details={
            'endpoint': request.path,
            'limit_hit': e.description,
            'method': request.method
        },
        severity='WARNING'
    )
    # 'e.description' contains the string "10 per 1 minute"
    return jsonify({
        "status": "error",
        "message": f"Rate limit exceeded: {e.description}. Please try again later."
    }), 429
    

if __name__ == '__main__':
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000, 
        ssl_context=('cert.pem', 'key.pem')
    )