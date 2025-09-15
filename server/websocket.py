# websocket_manager.py
"""
Manages WebSocket connections and streaming events.
"""

class WebSocketManager:
    def __init__(self):
        self.active_connections = []
    def connect(self, websocket):
        self.active_connections.append(websocket)
    def disconnect(self, websocket):
        self.active_connections.remove(websocket)
    async def send_text(self, websocket, message: str):
        await websocket.send_text(message)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
