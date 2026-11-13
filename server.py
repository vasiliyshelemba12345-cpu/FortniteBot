import threading
import tkinter as tk
import customtkinter as ctk
import socket
import base64
import hashlib

ctk.set_appearance_mode("dark")

class RATPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Rocket Way - TEST Server")
        self.geometry("600x400")
        self.label = ctk.CTkLabel(self, text="Статус: Ожидание", font=("Arial", 20), text_color="red")
        self.label.pack(pady=50)
        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=20)
        
        threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 5555))
        server.listen(1)
        self.log("Сервер запущен. Ждем подключения...")
        
        while True:
            conn, addr = server.accept()
            self.log(f"ПОДКЛЮЧЕНИЕ ОТ: {addr}")
            data = conn.recv(1024)
            
            if b"Upgrade: websocket" in data:
                self.log("Получен WebSocket запрос!")
                key = ""
                for line in data.decode().split("\r\n"):
                    if "Sec-WebSocket-Key" in line:
                        key = line.split(": ")[1]
                        break
                if key:
                    accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
                    response = f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n"
                    conn.send(response.encode())
                    self.label.configure(text="Статус: ПОДКЛЮЧЕН!", text_color="green")
                    self.log("Рукопожатие прошло успешно. Клиент подключен.")
            else:
                self.log("Ошибка: запрос не является WebSocket.")

    def log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

if __name__ == "__main__":
    app = RATPanel()
    app.mainloop()