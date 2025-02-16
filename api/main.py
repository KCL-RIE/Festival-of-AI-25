# main.py
import asyncio
from fastapi import FastAPI, WebSocket
app = FastAPI()

# write a get method to return some text

connnectedUsers = 0
maxConnectedUsers = 2


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.websocket("/ws/tv/onloading")
async def websocket_tv_onloading(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            global connnectedUsers
            await websocket.send_text(str(connnectedUsers))
            await asyncio.sleep(1)  # Adjust the interval as needed
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()


@app.websocket("/ws/mobile")
async def websocket_mobile(websocket: WebSocket):
    global connnectedUsers
    if connnectedUsers >= maxConnectedUsers:
        await websocket.close()
        return
    else:
        connnectedUsers += 1
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Message text was: {data}, {connnectedUsers}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            connnectedUsers -= 1
