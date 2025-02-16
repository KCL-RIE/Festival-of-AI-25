# main.py
from fastapi import FastAPI, WebSocket
app = FastAPI()

# write a get method to return some text

connnectedUsers = 0
maxConnectedUsers = 2


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.websocket("/ws/mobile")
async def websocket_endpoint(websocket: WebSocket):
    if connnectedUsers >= maxConnectedUsers:
        await websocket.close()
        return
    else:
        connnectedUsers += 1
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}, {connnectedUsers}")
