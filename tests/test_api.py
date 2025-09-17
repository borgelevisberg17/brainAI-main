import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
import json
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app, SECRET_KEY, ALGORITHM
from jose import jwt

# Using TestClient runs the app in the same process as the tests
client = TestClient(app)

# Generate a valid token for a test user
def create_test_token():
    to_encode = {"sub": "testuser", "exp": datetime.utcnow() + timedelta(minutes=30)}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def test_websocket_chat_history_failure_is_fixed():
    """
    This test verifies that the bug is fixed.
    With the fix, the server should gracefully close the connection
    after a failed AI history initialization. The test asserts that
    a WebSocketDisconnect exception is raised when trying to receive
    data after the error, which proves the connection was closed.
    """
    token = create_test_token()
    uri = f"/ws/chat?token={token}"

    with patch('api.get_user_by_username', return_value={"username": "testuser", "password": "testpassword"}), \
         patch('api.load_memory', return_value=[{"role": "user", "text": "hello"}]), \
         patch('api.criar_chat') as mock_criar_chat:

        mock_chat_instance = MagicMock()
        mock_chat_instance.send_message.side_effect = Exception("AI history initialization failed")
        mock_criar_chat.return_value = mock_chat_instance

        # The test should now expect the connection to be closed gracefully.
        with client.websocket_connect(uri) as websocket:
            assert websocket.receive_json() == {"type": "user_info", "username": "testuser"}
            assert websocket.receive_json() == {"type": "chat_history", "messages": [{"role": "user", "text": "hello"}]}

            online_users_msg = websocket.receive_json()
            assert online_users_msg['type'] == 'online_users'
            assert 'testuser' in online_users_msg['users']

            assert websocket.receive_json() == {"type": "error", "message": "Não foi possível conectar ao AI. Histórico local disponível."}

            # With the fix applied, the server should have closed the connection.
            # Attempting to receive again should raise a WebSocketDisconnect exception.
            with pytest.raises(WebSocketDisconnect):
                websocket.receive_json()
