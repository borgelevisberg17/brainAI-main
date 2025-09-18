import os
import google.generativeai as genai
from google.generativeai import types
from constants.settings import PERSONALIDADE as persona
from dotenv import load_dotenv

load_dotenv()
# Pega a API key do ambiente
Gemini_api = os.getenv('GEMINI_API_KEY')

# Verifica se a chave foi encontrada
if not Gemini_api:
    raise ValueError("A variável de ambiente 'GEMINI_API_KEY' não foi definida.")

# Configurações do modelo
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]

# Inicializa o modelo
genai.configure(api_key=Gemini_api)
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    safety_settings=safety_settings,
    generation_config=generation_config,
    system_instruction=persona,
)

def criar_chat():
    return model.start_chat(history=[])