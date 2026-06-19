import os
import json

MEMORY_DIR = "data/memory"

def get_memory_path(user_id):
    """Gera o caminho absoluto do arquivo de histórico do usuário."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    return os.path.join(MEMORY_DIR, f"user_{user_id}.json")

def load_memory(user_id):
    """Carrega o histórico de mensagens do usuário ou retorna uma lista vazia."""
    path = get_memory_path(user_id)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        # Proteção contra falhas se o JSON do histórico estiver vazio ou malformado
        return []

def save_memory(user_id, history):
    """Salva a lista completa de histórico do usuário em formato JSON."""
    path = get_memory_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_message(user_id, role, text):
    """Adiciona uma nova mensagem (user ou ai) ao histórico persistente."""
    history = load_memory(user_id)
    history.append({"role": role, "text": text})
    save_memory(user_id, history)