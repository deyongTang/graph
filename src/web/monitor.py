import asyncio
import json
from typing import List, Dict, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a JSON message to all connected clients."""
        if not self.active_connections:
            return
            
        text_data = json.dumps(message, default=str)
        for connection in self.active_connections:
            try:
                await connection.send_text(text_data)
            except Exception as e:
                print(f"Error sending to websocket: {e}")
                # We might want to remove dead connections here, but for now let's keep it simple

# Global instance
manager = ConnectionManager()

async def emit_event(event_type: str, data: Dict[str, Any] = None):
    """
    Helper function to emit an event to the monitoring dashboard.
    
    Args:
        event_type: The type of event (e.g., 'workflow_start', 'step_start', 'log')
        data: Additional data associated with the event
    """
    if data is None:
        data = {}
        
    event = {
        "type": event_type,
        "timestamp": asyncio.get_event_loop().time(), # Simple timestamp
        "data": data
    }
    
    await manager.broadcast(event)
