// Lógica da Interface
const menuBtn = document.getElementById("menuBtn");
const newChatBtn = document.getElementById("newChatBtn");
const drawerMenu = document.getElementById("drawerMenu");
const drawerCloseBtn = document.getElementById("drawerCloseBtn");
const overlay = document.getElementById("overlay");
const chatLog = document.getElementById("chatLog");
const chatBox = document.getElementById("chatBox");
const msgInput = document.getElementById("msgInput");
const sendBtn = document.getElementById("sendBtn");
const initialLogo = `<div class="initial-logo"><svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="currentColor" stroke-width="2" stroke-miterlimit="10"/><path d="M17.5 6.5L6.5 17.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>`;

// Toggle drawer menu
const toggleDrawer = () => {
    drawerMenu.classList.toggle("open");
    overlay.classList.toggle("open");
};

menuBtn.addEventListener("click", toggleDrawer);
drawerCloseBtn.addEventListener("click", toggleDrawer);
overlay.addEventListener("click", toggleDrawer);

// Clear chat
newChatBtn.addEventListener("click", () => {
    fetch("/new_chat", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            chatLog.innerHTML = initialLogo;
            const username = getCurrentUsername();
            localStorage.removeItem(`chat_${username}`); // Clear local storage
            localStorage.removeItem(`unsent_${username}`); // Clear unsent messages
        })
        .catch(err => console.error("Error clearing chat:", err));
});

// Add message to UI
const addMessage = (role, text) => {
    if (chatLog.querySelector(".initial-logo")) {
        chatLog.innerHTML = "";
    }

    const msgElement = document.createElement("li");
    msgElement.classList.add("message", role);

    if (role === "ai") {
        const parsedMarkdown = DOMPurify.sanitize(
            marked.parse(text, { breaks: true })
        );
        msgElement.innerHTML = `<div class="ai-content">${parsedMarkdown}</div>`;
    } else {
        msgElement.textContent = text; // User messages as plain text
    }

    chatLog.appendChild(msgElement);
    chatBox.scrollTop = chatBox.scrollHeight;

    // Save to localStorage (except for error messages)
    if (role !== "error") {
        const username = getCurrentUsername();
        saveMessageToLocal(username, { role, text });
    }
};

// Load chat history from localStorage
function loadLocalChatHistory() {
    const username = getCurrentUsername();
    const history = JSON.parse(localStorage.getItem(`chat_${username}`)) || [];
    chatLog.innerHTML = history.length ? "" : initialLogo; // Show logo if empty
    history.forEach(msg => addMessage(msg.role, msg.text));
}

// Save message to localStorage
function saveMessageToLocal(username, message) {
    const history = JSON.parse(localStorage.getItem(`chat_${username}`)) || [];
    history.push(message);
    localStorage.setItem(`chat_${username}`, JSON.stringify(history));
}

// Queue unsent messages for offline sending
function queueUnsentMessage(username, message) {
    const unsent = JSON.parse(localStorage.getItem(`unsent_${username}`)) || [];
    unsent.push(message);
    localStorage.setItem(`unsent_${username}`, JSON.stringify(unsent));
}

// Send queued messages on reconnect
function sendUnsentMessages(socket) {
    const username = getCurrentUsername();
    const unsent = JSON.parse(localStorage.getItem(`unsent_${username}`)) || [];
    unsent.forEach(message => {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(message.text);
        }
    });
    localStorage.removeItem(`unsent_${username}`); // Clear queue
}

// Lógica do Backend
function getCookie(nome) {
    const cookies = document.cookie.split(";");
    for (let c of cookies) {
        const [chave, valor] = c.trim().split("=");
        if (chave === nome) return valor;
    }
    return null;
}

// Get current username
function getCurrentUsername() {
    return localStorage.getItem("current_username") || "default_user";
}

const token = getCookie("token");
if (!token) {
    window.location.href = "/login";
}

let socket = new WebSocket(`ws://${location.host}/ws/chat?token=${token}`);

// WebSocket event handlers
socket.onopen = () => {
    console.log("✅ Conectado ao BrainAI via WebSocket");
    sendUnsentMessages(socket); // Send any queued messages
};

socket.onmessage = event => {
    try {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);
        if (data.type === "online_users") {
            const lista = document.getElementById("usuariosOnline");
            lista.innerHTML = "";
            data.users.forEach(user => {
                const li = document.createElement("li");
                li.textContent = `👤 ${user}`;
                lista.appendChild(li);
            });
        } else if (data.type === "user_info") {
            document.getElementById("userName").textContent =
                data.username || "Usuário";
            localStorage.setItem("current_username", data.username); // Store username
            loadLocalChatHistory(); // Load local history on connection
        } else if (data.type === "chat_history") {
            const username = getCurrentUsername();
            localStorage.setItem(
                `chat_${username}`,
                JSON.stringify(data.messages)
            ); // Sync server history
            loadLocalChatHistory();
        } else if (data.type === "error") {
            addMessage("ai", data.message); // Display error messages from backend
        } else {
            addMessage("ai", event.data);
        }
    } catch (e) {
        console.error("Error parsing WebSocket message:", e);
        addMessage("ai", `${event.data}`);
    }
};

socket.onclose = () => {
    console.warn("🔌 Conexão encerrada");
    addMessage(
        "ai",
        "A conexão foi encerrada. Suas mensagens estão salvas localmente."
    );
    loadLocalChatHistory(); // Show cached messages
    tryReconnect(); // Attempt reconnection
};

// Reconnection logic
function tryReconnect() {
    if (socket.readyState !== WebSocket.OPEN) {
        socket = new WebSocket(`ws://${location.host}/ws/chat?token=${token}`);
        socket.onopen = () => {
            console.log("✅ Reconectado ao BrainAI via WebSocket");
            sendUnsentMessages(socket);
        };
        socket.onmessage = socket.onmessage; // Reuse existing handler
        socket.onclose = () => {
            console.warn(
                "🔌 Tentativa de reconexão falhou, tentando novamente em 5s..."
            );
            setTimeout(tryReconnect, 5000); // Retry every 5 seconds
        };
    }
}

// Send message
function enviar() {
    const texto = msgInput.value.trim();
    if (texto !== "") {
        const username = getCurrentUsername();
        const message = { role: "user", text: texto };
        addMessage("user", texto);
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(texto);
            sendUnsentMessages(socket);
        } else {
            queueUnsentMessage(username, message);
            console.log("Offline: Mensagem salva para sincronização");
            addMessage(
                "ai",
                "Mensagem salva localmente. Será enviada quando a conexão for restaurada."
            );
        }
        msgInput.value = "";
    }
}

sendBtn.addEventListener("click", enviar);
msgInput.addEventListener("keydown", e => {
    if (e.key === "Enter") {
        e.preventDefault();
        enviar();
    }
});

// Logout
function logout() {
    fetch("/logout", { method: "POST" })
        .then(() => {
            document.cookie = "token=; path=/; max-age=0";
            window.location.href = "/login";
        })
        .catch(err => {
            console.error("Erro no logout:", err);
            document.cookie = "token=; path=/; max-age=0";
            window.location.href = "/login";
        });
}

// Load local history on page load
window.addEventListener("load", () => {
    loadLocalChatHistory();
    if (!navigator.onLine) {
        console.log("Offline: Carregando mensagens salvas");
        addMessage(
            "ai",
            "Você está offline. Mensagens salvas estão sendo exibidas."
        );
    }
});

// Monitor online/offline status
window.addEventListener("online", () => {
    console.log("Online: Tentando reconectar...");
    tryReconnect();
});
window.addEventListener("offline", () => {
    console.log("Offline: Salvando mensagens localmente");
    addMessage("ai", "Você está offline. Mensagens serão salvas localmente.");
});
