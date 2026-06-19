import os
from google import genai
from google.genai import types
from constants.settings import PERSONALIDADE as persona
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Pega a API key do ambiente
Gemini_api = os.getenv('GEMINI_API_KEY')

# Verifica se a chave foi encontrada
if not Gemini_api:
    raise ValueError("A variável de ambiente 'GEMINI_API_KEY' não foi definida.")

# Inicializa o cliente com o novo SDK
client = genai.Client(api_key=Gemini_api)

# Configurações de geração e segurança usando a nova estrutura de tipos
config = types.GenerateContentConfig(
    temperature=1.0,
    top_p=0.95,
    top_k=64,
    max_output_tokens=8192,
    response_mime_type="text/plain",
    system_instruction=persona,
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
    ]
)

# Definimos o nome do modelo que você está usando
MODEL_NAME = "gemini-2.0-flash"

def criar_chat():
    """
    Cria e retorna uma nova sessão de chat interativa e contínua 
    utilizando o novo SDK do Google GenAI.
    """
    # No novo SDK, a sessão de chat mantém o histórico e aceita a configuração diretamente
    return client.chats.create(
        model=MODEL_NAME,
        config=config
    )