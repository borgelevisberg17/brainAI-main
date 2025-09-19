# Projeto Chat IA com FastAPI e Gemini

Este é um projeto de um assistente de IA que utiliza FastAPI para o backend, Gemini como modelo de linguagem, e uma interface de frontend simples para interação. O projeto também inclui autenticação de usuário e um chat em tempo real utilizando WebSockets.

## ✨ Funcionalidades

- **Backend com FastAPI:** Um backend robusto e rápido para servir a aplicação.
- **Modelo de Linguagem Gemini:** Utiliza o modelo de linguagem Gemini da Google para gerar respostas inteligentes.
- **Autenticação de Usuário:** Sistema de registro e login de usuários com tokens JWT.
- **Chat em Tempo Real:** Comunicação em tempo real com o assistente de IA através de WebSockets.
- **Endpoint para Portfólio:** Um endpoint público para ser consumido por um portfólio ou outra aplicação externa.
- **Interface de Frontend:** Uma interface de usuário simples para login e chat.
- **Containerização com Docker:** O projeto pode ser facilmente containerizado utilizando o Dockerfile incluso.

## 🚀 Instalação

Para rodar este projeto localmente, siga os passos abaixo:

1. **Clone o repositório:**
   ```bash
   git clone <url_do_repositorio>
   cd <nome_do_repositorio>
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente:**
   - Crie um arquivo `.env` na raiz do projeto.
   - Adicione as seguintes variáveis de ambiente ao arquivo `.env`:
     ```
     GEMINI_API_KEY="sua_chave_de_api_do_gemini"
     SECRET_KEY="sua_chave_secreta_para_jwt"
     ```

##  kullanım

Para iniciar a aplicação, execute o seguinte comando na raiz do projeto:

```bash
uvicorn api:app --reload
```

A aplicação estará disponível em `http://127.0.0.1:8000`.

## 🔑 Variáveis de Ambiente

- `GEMINI_API_KEY`: A sua chave de API do Google Gemini.
- `SECRET_KEY`: Uma chave secreta para a codificação e decodificação de tokens JWT.

## Endpoints da API

- `GET /`: Página principal do chat (requer autenticação).
- `GET /login`: Página de login.
- `POST /register`: Rota para registrar um novo usuário.
- `POST /token`: Rota para obter um token de acesso (login).
- `POST /logout`: Rota para invalidar um token (logout).
- `POST /api/portfolio/chat`: Endpoint público para o assistente do portfólio.
- `WS /ws/chat`: WebSocket para o chat em tempo real (requer autenticação).
