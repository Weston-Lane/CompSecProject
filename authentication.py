from flask import Flask, request, jsonify, render_template, make_response
import bcrypt
import jsonUtils
from User import User
import re
import time
from enum import Enum
from DataBase import DataBase
from SecurityLogger import SecurityLogger
from SessionManager import SessionManager
LOCK_OUT_TIME = 900 #15min
LOGIN_ATTEMPTS_MAX = 5
class ValidationStatus(Enum):
    VALID = 0
    INVALID_USER_INPUT = 1
    INVALID_PASS_INPUT = 2
    INVALID_EMAIL_INPUT = 3
    PASS_NOT_MATCH = 4
    ALREADY_EXISTS = 5
    TOO_MANY_ATTEMPTS = 6

def registerUser(data):
    userInfo = {
        "username": data.get('username'),
        "password": data.get('password'),
        "passwordMatch": data.get('passwordMatch'),
        "role": "",
        "email": data.get('email')
    }

    if (error := ValidateInput(userInfo)) != ValidationStatus.VALID:        
        match error:
            case ValidationStatus.INVALID_USER_INPUT:
                return jsonify({"status": "error", "message": "Username Must be 3-20 characters, alphanumeric + underscore"}), 401
            case ValidationStatus.INVALID_PASS_INPUT:
                return jsonify({"status": "error", "message": "Password must be: Minimum 12 characters, "
                "At least 1 uppercase letter,"
                "At least 1 lowercase letter,"
                "At least 1 number,"
                "At least 1 special character (!@#$%^&*) "}), 400
            case ValidationStatus.INVALID_EMAIL_INPUT:
                return jsonify({"status": "error", "message": "Invalid email format"}), 400
            case ValidationStatus.PASS_NOT_MATCH:
                return jsonify({"status": "error", "message": "Passwords do not match"}), 409
            case ValidationStatus.ALREADY_EXISTS:
                return jsonify({"status": "error", "message": "Username or email already exists"}), 409
            case _:
                return jsonify({"status": "error", "message": "Unknown server error"}), 500

    db = DataBase.get_instance()
    if len(db.users) == 0 :
        userInfo['role'] = "admin"
    else:
        userInfo['role'] = "user"

    AddUserToDB(userInfo)
    return jsonify({"status": "success", "message": "Account Registered"}), 200
  
def ValidateInput(userInfo):
    db = DataBase.get_instance() 

    username = userInfo.get('username', '')
    email = userInfo.get('email', '')
    password = userInfo.get('password', '')
    passwordMatch = userInfo.get('passwordMatch', '')

    if any(u.get('username') == username for u in db.users):
        return ValidationStatus.ALREADY_EXISTS
    
    validUsernamePattern = r"^[a-zA-Z0-9_]{3,20}$"
    if not re.match(validUsernamePattern, username):
        return ValidationStatus.INVALID_USER_INPUT
    
    if any(u.get('email') == email for u in db.users):
        return ValidationStatus.ALREADY_EXISTS

    validEmailPattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(validEmailPattern, email):
        return ValidationStatus.INVALID_EMAIL_INPUT

    if password != passwordMatch:
        return ValidationStatus.PASS_NOT_MATCH
    
    validPasswordPattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{12,}$"
    if not re.match(validPasswordPattern, password):
        return ValidationStatus.INVALID_PASS_INPUT
    
    return ValidationStatus.VALID

def AddUserToDB(userInfo):
    salt = bcrypt.gensalt(rounds = 12)
    hashedPass = bcrypt.hashpw(userInfo['password'].encode('utf-8'), salt)
    newUser = User(
        username = userInfo['username'],
        email = userInfo['email'],
        password_hash = hashedPass.decode('utf-8'),
        role = userInfo['role']
    )
    db = DataBase.get_instance()    
    db.AddUser(newUser)
    db.SaveUsers()

def LoginUser(data):
    userInfo = {
        "username": data.get('username'),
        "password": data.get('password'),
    }

    if(error := ValidateCredentials(userInfo)):
        securityLogger = SecurityLogger.get_instance()
        securityLogger.log_event(event_type="Failed Login Attempt", 
                                 user_id= userInfo['username'], 
                                details={
                                "reason": error.name, # Evaluates to 'INVALID_USER_INPUT', 'PASS_NOT_MATCH', etc.
                                "provided_username": userInfo.get('username')
                                },
                                severity="WARNING"
                                )
        match error:
            case ValidationStatus.INVALID_USER_INPUT:
                return jsonify({"status": "error", "message": "Invalid Username or Password"}), 401
            case ValidationStatus.PASS_NOT_MATCH:
                return jsonify({"status": "error", "message": "Invalid Username or Password"}), 401
            case ValidationStatus.TOO_MANY_ATTEMPTS:
                return jsonify({"status": "error", "message": "Too many attempts, lockout"}), 403
        
    session_manager = SessionManager.get_instance()
    token = session_manager.create_session(user_id=userInfo['username'])

    db = DataBase.get_instance()
    user = db.FindUser(userInfo['username'])
    
    # Determine the correct landing page
    if user.role == 'admin':
        redirect_url = '/admin'
    elif user.role == 'user':
        redirect_url = '/dashboard'
    else:
        redirect_url = '/guest'
    # ---------------------------------------------------

    response = make_response(jsonify({
        "status": "success", 
        "message": "Successful Login",
        "redirect": redirect_url  # <-- Send the URL to the frontend
    }))
    
    response.set_cookie(
        'session_token',
        token,
        httponly=True,    
        secure=True,      
        samesite='Strict',
        max_age=1800      
    )
    
    # 4. Return the response and the 200 OK status
    return response, 200
            

def ValidateCredentials(userInfo):
    db = DataBase.get_instance()
    user = db.FindUser(userInfo.get('username'))
    if user is None:
        return ValidationStatus.INVALID_USER_INPUT
    
    if user.locked_until is not None:
        if time.time() < user.locked_until:
            return ValidationStatus.TOO_MANY_ATTEMPTS
        else:
            user.locked_until = None
            user.failed_attempts = 0
        
    inputPass = userInfo.get('password').encode("utf-8")
    storedHash = user.password_hash.encode('utf-8')
    if not bcrypt.checkpw(inputPass, storedHash):
        user.failed_attempts += 1
        if user.failed_attempts >= LOGIN_ATTEMPTS_MAX:
            user.locked_until = time.time() + LOCK_OUT_TIME

        db.UpdateUser(user)    
        return ValidationStatus.PASS_NOT_MATCH
    
    if user.failed_attempts > 0:
        user.failed_attempts = 0
        user.locked_until = None
        db.UpdateUser(user)

    return ValidationStatus.VALID
    
