from flask import Flask, request, jsonify, render_template
from flask_cors import CORS # Allows your frontend to talk to the backend
import bcrypt
import json
import os

app = Flask(__name__)
CORS(app) # Prevents "Cross-Origin" errors during local development

# Helper to read/write your JSON "Database"
def write_json(filename, data):
    with open(f'data/{filename}.json', 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password').encode('utf-8')
    
    # Hash the password
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    
    # Store in users.json (Simplified logic)
    # In a real app, check if user exists first!
    user_record = {"username": username, "password": hashed.decode('utf-8')}
    write_json('users', [user_record]) 
    
    return jsonify({"status": "success", "message": "User created"}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)