from flask import Flask, request, jsonify, render_template, g, make_response, redirect, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import html 
import os
import os 
from dotenv import load_dotenv
import io
import re
import filetype
import authentication
from SecurityLogger import SecurityLogger
from SessionManager import SessionManager
from DataBase import DataBase
from encryption_utils import storage
from Roles import login_required, require_roles

############################################################################
#           DELETE AFTER DONE!
#           ADMIN USER : admin
#           ADMIN PASS: Password!123
#           
#           Other User Names and roles are: User, Guest 
#           Passwords: Password!123
#
############################################################################

load_dotenv()

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(32).hex()) 

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

@app.route('/admin')
@login_required
@require_roles('admin')
def admin_dashboard_page():
    return render_template('admin/dashboard.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def registerUser():
    return authentication.registerUser(request.json)




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

@app.route('/api/admin/update-role', methods=['POST'])
@login_required
@require_roles('admin')
def update_user_role():
    data = request.json
    target_user = data.get('username')
    new_role = data.get('role')

    if not target_user or not new_role:
        return jsonify({"error": "Missing username or role"}), 400

    # Ensure they are only picking valid roles
    valid_roles = ['admin', 'user', 'guest']
    if new_role not in valid_roles:
        SecurityLogger.get_instance().log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            details={"reason": "Invalid role specified", "input": new_role},
            severity="WARNING", log_type="security"
        )
        return jsonify({"error": "Invalid role specified"}), 400

    # Safety mechanism: Prevent the active admin from demoting themselves
    if target_user == g.user_id and new_role != 'admin':
        return jsonify({"error": "You cannot demote your own admin account."}), 403

    db = DataBase.get_instance()
    success = db.UpdateUserRole(target_user, new_role)

    if success:
        SecurityLogger.get_instance().log_event(
            event_type="SECURITY_CONFIG_CHANGE",
            details={"action": "role_update", "target_user": target_user, "new_role": new_role},
            severity="INFO", log_type="security"
        )
        return jsonify({"message": f"Successfully updated {target_user} to {new_role}"}), 200
    else:
        return jsonify({"error": "User not found in database"}), 404

@app.route('/dashboard')
@login_required
@require_roles('user', 'admin') # Let admins see it for testing
def dashboard():
    return render_template('dashboard.html')

@app.route('/guest')
@login_required
@require_roles('guest', 'admin') # Let admins see it for testing
def guest_dashboard_page():
    return render_template('dashboard_guest.html')

@app.route('/register')
def goToRegisterPage():
    return render_template('register.html')

@app.route('/')
def goToLoginPage():
    return render_template('index.html')


########################## Document Routing ###################################

# Ensure this matches the directory used in your code
UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)



def sanitize_input(user_input):
    """Escape HTML special characters"""
    if not user_input:
        return ""
    return html.escape(user_input)

def sanitize_output(data):
    """Sanitize before rendering"""
    if isinstance(data, str):
        return html.escape(data)
    return data


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not getattr(g, 'user_id', None):
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'document' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['document']

    if not allowed_file(file.filename):
        SecurityLogger.get_instance().log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            details={"reason": "Disallowed file extension", "filename": file.filename},
            severity="WARNING", log_type="security"
        )
        return jsonify({"error": "File type not allowed"}), 400
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Strip directory traversal characters
    safe_path_name = secure_filename(file.filename)
    
    #Run the string through XSS sanitization function
    sanitized_filename = sanitize_input(safe_path_name)
    
    # 3. Fallback for edge cases
    if not sanitized_filename:
        sanitized_filename = "unnamed_document"
    # ----------------------------------------

    # Encrypt the file
    file_data = file.read()
    # kind = filetype.guess(file_data)
    # if kind is None or kind.extension not in ALLOWED_EXTENSIONS:
    #     return jsonify({"error": "Spoofed file detected"}), 400
    encrypted_data = storage.encrypt_bytes(file_data)

    # Save physical file to disk
    file_id = os.urandom(8).hex() 
    storage_path = os.path.join(UPLOAD_DIR, file_id)
    with open(storage_path, 'wb') as f:
        f.write(encrypted_data)

    # Add metadata to the DataBase
    db = DataBase.get_instance()
    db.AddDocument(
        doc_id=file_id, 
        original_filename=sanitized_filename,  
        content_type=file.content_type, 
        owner_id=g.user_id
    )

    SecurityLogger.get_instance().log_event(
        event_type="DATA_CREATE",
        details={"file_id": file_id, "filename": sanitized_filename},
        severity="INFO", log_type="access"
    )

    return jsonify({
        "message": "File encrypted and uploaded securely", 
        "file_id": file_id
    }), 200

@app.route('/api/my-files', methods=['GET'])
def get_my_files():
    if not getattr(g, 'user_id', None):
        return jsonify({"error": "Unauthorized"}), 401
        
    db = DataBase.get_instance()
    user_docs = db.GetUserDocuments(g.user_id)
    
    # Format the data for the frontend
    files_to_return = []
    for doc in user_docs:
        files_to_return.append({
            "file_id": doc['file_id'],
            "filename": doc.get('display_name', doc.get('original_filename')),
            "shared_with": doc.get('shared_with', [])
        })
            
    return jsonify({"files": files_to_return}), 200

@app.route('/api/shared-with-me', methods=['GET'])
def get_shared_files():
    if not getattr(g, 'user_id', None):
        return jsonify({"error": "Unauthorized"}), 401
        
    db = DataBase.get_instance()
    shared_docs = db.GetSharedDocuments(g.user_id)
    
    files_to_return = []
    for doc in shared_docs:
        files_to_return.append({
            "file_id": doc['file_id'],
            "filename": doc.get('display_name', doc.get('original_filename')),
            "owner_id": doc['owner_id']
        })
            
    return jsonify({"files": files_to_return}), 200

@app.route('/api/view/<file_id>', methods=['GET'])
def view_file(file_id):
    if not getattr(g, 'user_id', None):
        return jsonify({"error": "Unauthorized"}), 401

    db = DataBase.get_instance()
    doc_meta = db.GetDocument(file_id)
    
    if not doc_meta:
        return jsonify({"error": "File not found"}), 404

    # Authorization Check: Is the user the owner OR in the shared_with list?
    is_owner = doc_meta.get('owner_id') == g.user_id
    is_shared = g.user_id in doc_meta.get('shared_with', [])

    if not (is_owner or is_shared):
        SecurityLogger.get_instance().log_event(
            event_type="AUTHORIZATION_FAILURE",
            details={"action": "read_file", "file_id": file_id},
            severity="WARNING", log_type="security"
        )
        return jsonify({"error": "Forbidden: You do not have permission"}), 403

    # Decrypt and Serve
    storage_path = os.path.join(UPLOAD_DIR, file_id)
    if not os.path.exists(storage_path):
        return jsonify({"error": "Encrypted file missing from disk"}), 500

    with open(storage_path, 'rb') as f:
        encrypted_data = f.read()

    try:
       decrypted_data = storage.decrypt_bytes(encrypted_data)
    except Exception as e:
        return jsonify({"error": "Decryption failed"}), 500

    SecurityLogger.get_instance().log_event(
        event_type="DATA_READ",
        details={"file_id": file_id, "action": "view_or_download"},
        severity="INFO", log_type="access"
    )

    return send_file(
        io.BytesIO(decrypted_data),
        mimetype=doc_meta['content_type'],
        as_attachment=True, # Set to True to force download
        download_name=doc_meta['original_filename']
    )

@app.route('/api/share', methods=['POST'])
def share_file():
    if not getattr(g, 'user_id', None):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    file_id = data.get('file_id')
    target_user = data.get('target_user')
    
    if not target_user or not re.match(r"^[a-zA-Z0-9_]{3,20}$", target_user):
        SecurityLogger.get_instance().log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            details={"reason": "Invalid username format for sharing"},
            severity="WARNING", log_type="security"
        )
        return jsonify({"error": "Invalid username format"}), 400

    if not file_id or not target_user:
        return jsonify({"error": "Missing file_id or target_user"}), 400

    db = DataBase.get_instance()
    
    # Optional: Verify the target_user actually exists in the system
    # if not db.FindUser(target_user):
    #     return jsonify({"error": "Target user does not exist"}), 404

    success = db.ShareDocument(file_id, g.user_id, target_user)

    if success:
        SecurityLogger.get_instance().log_event(
            event_type="DATA_UPDATE",
            details={"action": "share_file", "file_id": file_id, "shared_with": target_user},
            severity="INFO", log_type="access"
        )
        return jsonify({"message": f"Successfully shared with {target_user}"}), 200
    else:
        return jsonify({"error": "Failed to share. Check permissions."}), 403


@app.route('/api/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    if not getattr(g, 'user_id', None):
        return jsonify({"error": "Unauthorized"}), 401

    db = DataBase.get_instance()
    success = db.DeleteDocument(file_id, g.user_id)
    
    if not success:
        SecurityLogger.get_instance().log_event(
            event_type="AUTHORIZATION_FAILURE",
            details={"action": "delete_file", "file_id": file_id},
            severity="WARNING", log_type="security"
        )
        return jsonify({"error": "Forbidden or file not found"}), 403

    # Remove physical file
    storage_path = os.path.join(UPLOAD_DIR, file_id)
    if os.path.exists(storage_path):
        try:
            os.remove(storage_path)
        except OSError as e:
            print(f"Error deleting physical file {file_id}: {e}")
            return jsonify({"error": "Database updated, but physical file deletion failed"}), 500
        
    SecurityLogger.get_instance().log_event(
        event_type="DATA_DELETE",
        details={"file_id": file_id},
        severity="INFO", log_type="access"
    )
    return jsonify({"message": "Document deleted successfully"}), 200

@app.route('/api/download/<file_id>', methods=['GET'])
@login_required
@require_roles('admin', 'user', 'guest')
def download_file(file_id):
    db = DataBase.get_instance()
    doc_meta = db.GetDocument(file_id)
    
    if not doc_meta:
        return jsonify({"error": "File not found"}), 404

    # Permission check (Same as view)
    user = db.FindUser(g.user_id)
    is_admin = user and user.role == 'admin'
    is_owner = doc_meta.get('owner_id') == g.user_id
    is_shared = g.user_id in doc_meta.get('shared_with', [])

    if not (is_admin or is_owner or is_shared):
        return jsonify({"error": "Forbidden"}), 403

    storage_path = os.path.join(UPLOAD_DIR, file_id)
    with open(storage_path, 'rb') as f:
        encrypted_data = f.read()

    try:
        decrypted_data = storage.decrypt_bytes(encrypted_data)
    except Exception:
        return jsonify({"error": "Decryption failed"}), 500

    # Key change: as_attachment=True forces the 'Save As' dialog
    return send_file(
        io.BytesIO(decrypted_data),
        mimetype=doc_meta['content_type'],
        as_attachment=True, 
        download_name=doc_meta['original_filename']
    )

@app.route('/api/admin/all-files', methods=['GET'])
@login_required
@require_roles('admin')
def get_all_system_files():
    db = DataBase.get_instance()
    
    files_to_return = []
    for doc in db.documents:
        files_to_return.append({
            "file_id": doc['file_id'],
           "filename": doc.get('display_name', doc.get('original_filename')),
            "owner_id": doc['owner_id'],
            "shared_with": doc.get('shared_with', [])
        })
            
    return jsonify({"files": files_to_return}), 200


@app.route('/api/admin/users', methods=['GET'])
@login_required
@require_roles('admin')
def get_all_users():
    db = DataBase.get_instance()
    
    users_to_return = []
    for user in db.users:
        # Check if the database loaded it as a Dictionary
        if isinstance(user, dict):
            users_to_return.append({
                "username": user.get('username', 'Unknown'),
                "email": user.get('email', 'Unknown'),
                "role": user.get('role', 'user'),
                "locked_until": user.get('locked_until', None),
                "failed_attempts": user.get('failed_attempts', 0)
            })
        # Check if it was stored as a Python Object
        else:
            users_to_return.append({
                "username": getattr(user, 'username', 'Unknown'),
                "email": getattr(user, 'email', 'Unknown'),
                "role": getattr(user, 'role', 'user'),
                "locked_until": getattr(user, 'locked_until', None),
                "failed_attempts": getattr(user, 'failed_attempts', 0)
            })
            
    return jsonify({"users": users_to_return}), 200

########################## Entry Point ###################################
if __name__ == '__main__':

    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000, 
        ssl_context=('cert.pem', 'key.pem')
    )