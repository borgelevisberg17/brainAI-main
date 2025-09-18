from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from core.core import criar_chat
from utils.memory_manager import load_memory, add_message
from utils.user_manager import authenticate_user, get_user_by_username
import asyncio
import os
from typing import List
from fastapi.websockets import WebSocketState
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request, Body
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
from constants.settings import PERSONALIDADE

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend/static/"), name="static")

# 🧠 Múltiplas conexões de usuários
active_connections = {}

# ❌ Blacklist para tokens expirados manualmente
token_blacklist = set()
active_connections = {}
online_users: List[str] = []
user_sockets: List[WebSocket] = []
# 🔍 Verifica e retorna o usuário logado (e rejeita tokens na blacklist)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    if token in token_blacklist:
        raise HTTPException(status_code=401, detail="Token inválido – logout feito")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return get_user_by_username(username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def broadcast_online_users():
    for ws in user_sockets:
        if ws.application_state == WebSocketState.CONNECTED:
            await ws.send_json({"type": "online_users", "users": online_users})
            
# 🏠 Página principal
@app.get("/")
async def serve_index(request: Request):
    token = request.cookies.get("token")
    if not token or token in token_blacklist:
        return RedirectResponse("/login", status_code=302)
    try:
        await get_current_user(token)
    except:
        return RedirectResponse("/login", status_code=302)
    return FileResponse(os.path.join("frontend", "index.html"))

# 🔐 Página de login
@app.get("/login")
async def serve_login():
    return FileResponse(os.path.join("frontend", "login.html"))
from utils.user_manager import create_user, user_exists

@app.post("/register")
async def register(user: dict = Body(...)):
    username = user.get("username")
    password = user.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Usuário e senha são obrigatórios")

    if user_exists(username):
        raise HTTPException(status_code=400, detail="Usuário já existe")

    create_user(username, password)
    print(f"[DEBUG] Novo usuário criado: {username}")
    return {"message": "Usuário registrado com sucesso"}
# 🔑 Gera e retorna token
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print("[DEBUG] Tentando autenticar usuário...")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        print("[DEBUG] Falha na autenticação")
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user["username"], "exp": expire}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    print(f"[DEBUG] Token gerado para {user['username']}")
    return {"access_token": token, "token_type": "bearer"}

# 🚪 Logout fino – token entra na blacklist
@app.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("token")
    if token:
        token_blacklist.add(token)
        response.delete_cookie("token")
        print("[DEBUG] Token adicionado à blacklist e cookie removido")
    return {"message": "Logout realizado com sucesso."}
    
# 🚀 Endpoint público para o assistente do portfólio
@app.post("/api/portfolio/chat")
async def portfolio_chat(payload: dict = Body(...)):
    pergunta = payload.get("message")

    if not pergunta:
        raise HTTPException(status_code=400, detail="Mensagem vazia")

    try:
        chat = criar_chat(contexto="assistente_portfolio", personalidade=PERSONALIDADE)
        resposta = chat.send_message(pergunta)
        texto = resposta.candidates[0].content.parts[0].text.strip()
        # Limita a resposta a 200 caracteres
        resposta_texto = (texto[:197] + "...") if len(texto) > 200 else texto
    except Exception as e:
        print(f"[ERROR] Falha no assistente do portfólio: {e}")
        resposta_texto = "Desculpe, estou offline no momento."

    return {"reply": resposta_texto}
    
# 💬 WebSocket autenticado
# In api.py, /ws/chat endpoint
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token or token in token_blacklist:
        print("[DEBUG] Conexão recusada: token inválido ou logout feito")
        await websocket.close(code=1008)
        return

    try:
        user = await get_current_user(token)
    except Exception as e:
        print(f"[DEBUG] Conexão recusada: token inválido – {e}")
        await websocket.close(code=1008)
        return

    await websocket.accept()
    user_id = user["username"]

    # Send user_info message
    await websocket.send_json({"type": "user_info", "username": user_id})

    # Send chat history even if AI initialization fails
    history = load_memory(user_id)
    await websocket.send_json({"type": "chat_history", "messages": history})

    if user_id not in online_users:
        online_users.append(user_id)
        user_sockets.append(websocket)
        await broadcast_online_users()

    print(f"[DEBUG] Conexão aceita para {user_id}")
    active_connections[user_id] = websocket

    # Initialize chat, but handle network errors
    chat = criar_chat()
    try:
        for h in history:
            chat.send_message(h["text"])  # Attempt to initialize chat history
    except Exception as e:
        print(f"[DEBUG] Falha ao inicializar histórico no AI: {e}")
        await websocket.send_json({"type": "error", "message": "Não foi possível conectar ao AI. Histórico local disponível."})
        await websocket.close()
        return

    try:
        while True:
            pergunta = await websocket.receive_text()
            print(f"[DEBUG] Pergunta recebida de {user_id}: {pergunta}")

            add_message(user_id, "user", pergunta)

            try:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(None, chat.send_message, pergunta)
                resposta = response.candidates[0].content.parts[0].text.strip()
            except Exception as e:
                print(f"[ERROR] Falha ao obter resposta do AI: {e}")
                resposta = "Desculpe, estou offline. Sua mensagem foi salva e será respondida quando a conexão for restaurada."
                await websocket.send_json({"type": "error", "message": resposta})

            add_message(user_id, "ai", resposta)
            await websocket.send_text(resposta)

    except WebSocketDisconnect:
        print(f"[DEBUG] Desconectado: {user_id}")
    except Exception as e:
        print(f"[ERROR] Erro inesperado: {e}")
        await websocket.send_json({"type": "error", "message": f"Erro interno: {e}"})
    finally:
        active_connections.pop(user_id, None)
        if user_id in online_users:
            online_users.remove(user_id)
            user_sockets.remove(websocket)
            await broadcast_online_users()
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except Exception as e:
                print(f"[DEBUG] Erro ao fechar WebSocket: {e}")