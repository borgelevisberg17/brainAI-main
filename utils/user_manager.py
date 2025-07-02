import json
import os
from hashlib import sha256

USER_DB = "data/users/users.json"

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USER_DB):
        return {}
    with open(USER_DB, "r") as f:
        return json.load(f)

def save_users(users):
    os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=2)

def user_exists(username):
    users = load_users()
    return username in users

def create_user(username, password):
    users = load_users()
    users[username] = {
        "username": username,
        "password": hash_password(password)
    }
    save_users(users)

def authenticate_user(username, password):
    users = load_users()
    hashed = hash_password(password)
    user = users.get(username)
    if user and user["password"] == hashed:
        return user
    return None

def get_user_by_username(username):
    users = load_users()
    return users.get(username)