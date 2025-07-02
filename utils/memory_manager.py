import os
import json

MEMORY_DIR = "data/memory"

def get_memory_path(user_id):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    return os.path.join(MEMORY_DIR, f"user_{user_id}.json")

def load_memory(user_id):
    path = get_memory_path(user_id)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(user_id, history):
    path = get_memory_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_message(user_id, role, text):
    history = load_memory(user_id)
    history.append({"role": role, "text": text})
    save_memory(user_id, history)