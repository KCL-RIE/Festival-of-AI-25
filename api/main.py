# main.py
import asyncio
from fastapi import FastAPI, WebSocket
app = FastAPI()

# write a get method to return some text

connectedUsers = 0
maxConnectedUsers = 2


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.websocket("/ws/tv/onloading")
async def websocket_tv_onloading(websocket: WebSocket):
    await websocket.accept()
    previous_connected_users = None
    try:
        while True:
            global connectedUsers
            if connectedUsers != previous_connected_users:
                await websocket.send_text(str(connectedUsers))
                previous_connected_users = connectedUsers
            await asyncio.sleep(1)  # Adjust the interval as needed
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()


@app.websocket("/ws/mobile")
async def websocket_mobile(websocket: WebSocket):
    global connectedUsers
    if connectedUsers >= maxConnectedUsers:
        await websocket.close()
        return
    else:
        connectedUsers += 1
        user_id = connectedUsers
        await websocket.accept()

        async def broadcast():
            for connection in app.connections:
                await connection.send_json({'userid': user_id, 'connectedUsers': connectedUsers})

        if not hasattr(app, 'connections'):
            app.connections = []

        app.connections.append(websocket)
        await broadcast()

        try:
            while True:
                data = await websocket.receive_text()
                await broadcast()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            connectedUsers -= 1
            app.connections.remove(websocket)
            await broadcast()
