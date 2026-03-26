from flask import Flask, request, jsonify, render_template
from flask_cors import CORS # Allows your frontend to talk to the backend
import bcrypt
import jsonUtils
import authentication
app = Flask(__name__)
CORS(app) # Prevents "Cross-Origin" errors during local development

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def registerUser():
    return authentication.registerUser(request.json)

import jwt
import datetime

# This should be a long, random string. Do not expose it in production.
app.config['SECRET_KEY'] = 'super-secret-key-for-project' 

@app.route('/api/login', methods=['POST'])
def login():
    return authentication.LoginUser(request.json)
    # data = request.json
    # username = data.get('username')
    # password = data.get('password').encode('utf-8')
    
    # users = jsonUtils.read_json('users')
    
    # # 1. Find the user in the database
    # user = next((u for u in users if u['username'] == username), None)
    
    # if not user:
    #     return jsonify({"status": "error", "message": "Invalid username or password"}), 401
        
    # # 2. Verify the password hash
    # if bcrypt.checkpw(password, user['password'].encode('utf-8')):
    #     # 3. Generate the JWT
    #     token = jwt.encode({
    #         'username': username,
    #         'role': user.get('role', 'user'),
    #         'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2) # Token expires in 2 hours
    #     }, app.config['SECRET_KEY'], algorithm="HS256")
        
    #     return jsonify({"status": "success", "token": token}), 200
    # else:
    #     return jsonify({"status": "error", "message": "Invalid username or password"}), 401
    
    # return jsonify({"status": "success", "message": "User created"}), 201

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/register')
def goToRegisterPage():
    return render_template('register.html')

@app.route('/')
def goToLoginPage():
    return render_template('index.html')
    

if __name__ == '__main__':
    app.run(debug=True, port=5000)