import json
import os
from hashlib import sha256

USER_DB = "data/users/users.json"

def hash_password(password):
    """Gera o hash SHA-256 de uma senha string."""
    return sha256(password.encode('utf-8')).hexdigest()

def load_users():
    """Carrega o dicionário de usuários do arquivo JSON."""
    if not os.path.exists(USER_DB):
        return {}
    try:
        with open(USER_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        # Se o arquivo estiver corrompido ou vazio, evita quebrar o app
        return {}

def save_users(users):
    """Salva o dicionário de usuários no arquivo JSON."""
    os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
    with open(USER_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def user_exists(username):
    """Verifica se um nome de usuário já está cadastrado."""
    users = load_users()
    return username in users

def create_user(username, password):
    """Cria um novo usuário salvando a senha criptografada em hash."""
    users = load_users()
    users[username] = {
        "username": username,
        "password": hash_password(password)
    }
    save_users(users)

def authenticate_user(username, password):
    """Autentica o usuário comparando o hash da senha fornecida."""
    users = load_users()
    hashed = hash_password(password)
    user = users.get(username)
    if user and user["password"] == hashed:
        return user
    return None

def get_user_by_username(username):
    """Retorna os dados públicos ou cadastrados de um usuário específico."""
    users = load_users()
    return users.get(username)