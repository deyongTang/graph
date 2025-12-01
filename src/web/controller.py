import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from src.web.schemas import Question, Answer
from src.web.service import ChatService
from src.web.monitor import manager
from src.conf import config
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(config.WEB_STATIC_DIR)), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可根据需要限定 origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
service = ChatService()


@app.get("/")
def read_root():
    return RedirectResponse("/static/index.html")


@app.post("/api/chat")
async def read_item(question: Question) -> Answer:
    answer = await service.chat(question.message)
    print("answer:", answer)
    print("answerType", type(answer))
    return Answer(message=answer)


@app.websocket("/ws/monitor")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run("src.web.controller:app", host="0.0.0.0", port=8086)
