import os
from google import genai
from google.genai import types
from constants.settings import PERSONALIDADE as persona
from dotenv import load_dotenv

load_dotenv()
# Pega a API key do ambiente
Gemini_api = os.getenv('GEMINI_API_KEY')

# Verifica se a chave foi encontrada
if not Gemini_api:
    raise ValueError("A variável de ambiente 'GEMINI_API_KEY' não foi definida.")

# Cria cliente
client = genai.Client(api_key=Gemini_api)

# Configurações do chat
modelAI = 'gemini-2.0-flash'
chat_config = types.GenerateContentConfig(system_instruction=persona)

# Função que retorna um novo chat configurado
def criar_chat():
    return client.chats.create(model=modelAI, config=chat_config)