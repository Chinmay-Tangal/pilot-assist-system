from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="Pilot Assist API")

# Allow our future React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🟢 Dashboard Connected! (Total: {len(self.active_connections)})")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"🔴 Dashboard Disconnected. (Total: {len(self.active_connections)})")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- Endpoints ---

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """The dashboard will connect to this endpoint to listen for live updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection open
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/telemetry")
async def update_telemetry(data: dict):
    """The Audio Pipeline sends the Llama 3.2 JSON here."""
    # Instantly broadcast the incoming data to any connected dashboards
    await manager.broadcast(json.dumps(data))
    return {"status": "success", "message": "Data broadcasted to dashboard"}

if __name__ == "__main__":
    import uvicorn
    print("Starting Pilot Assist API on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)