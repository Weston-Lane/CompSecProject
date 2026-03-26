from flask import Flask, request, jsonify, render_template
import bcrypt
import jsonUtils
import re
from enum import Enum

class ValidationStatus(Enum):
    VALID = 0
    INVALID_USER_INPUT = 1
    INVALID_PASS_INPUT = 2
    INVALID_EMAIL_INPUT = 3
    PASS_NOT_MATCH = 4
    ALREADY_EXISTS = 5

def registerUser(data):
    userInfo = {
        "username": data.get('username'),
        "password": data.get('password'),
        "passwordMatch": data.get('passwordMatch'),
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
            
    AddUserToDB(userInfo)
        
def ValidateInput(userInfo):
    users = jsonUtils.read_json('users')

    username = userInfo.get('username', '')
    email = userInfo.get('email', '')
    password = userInfo.get('password', '')
    passwordMatch = userInfo.get('passwordMatch', '')

    if any(u['username'] == username for u in users):
        return ValidationStatus.ALREADY_EXISTS
    
    validUsernamePattern = r"^[a-zA-Z0-9_]{3,20}$"
    if not re.match(validUsernamePattern, username):
        return ValidationStatus.INVALID_USER_INPUT
    
    if any(u['email'] == email for u in users):
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
    user = User(
        username = userInfo['username'],
        email = userInfo['email'],

    )