# main.py
import asyncio
from fastapi import FastAPI, WebSocket
app = FastAPI()

# write a get method to return some text

connectedUsers = 0
maxConnectedUsers = 2

gameState = {
    "connectedUsers": connectedUsers,
    "maxConnectedUsers": maxConnectedUsers,
    "connections": [],
    "difficulty": ""
}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.websocket("/ws/tv/onloading")
async def websocket_tv_onloading(websocket: WebSocket):
    await websocket.accept()
    previous_connected_users = None
    try:
        while True:
            if gameState["connectedUsers"] != previous_connected_users:
                await websocket.send_text(str(gameState["connectedUsers"]))
                previous_connected_users = gameState["connectedUsers"]
            await asyncio.sleep(1)  # Adjust the interval as needed
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()


@app.websocket("/ws/mobile")
async def websocket_mobile(websocket: WebSocket):
    if gameState["connectedUsers"] >= gameState["maxConnectedUsers"]:
        await websocket.close()
        return
    else:
        gameState["connectedUsers"] += 1
        user_id = gameState["connectedUsers"]
        await websocket.accept()

        async def broadcast():
            for connection in gameState["connections"]:
                await connection.send_json({'userid': user_id, 'connectedUsers': gameState["connectedUsers"], 'difficulty': gameState["difficulty"]})

        gameState["connections"].append(websocket)
        await broadcast()

        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "difficulty":
                    gameState["difficulty"] = data["difficulty"]
                await broadcast()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            gameState["connectedUsers"] -= 1
            gameState["connections"].remove(websocket)
            await broadcast()


@app.websocket("/ws/robotcontrol")
async def websocket_robotcontrol(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()
