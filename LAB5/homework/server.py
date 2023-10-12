import socket
import threading
import json
import os

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_files = 'SERVER_FILES'
        os.makedirs(self.server_files, exist_ok=True)
        self.clients = []
        self.chatrooms = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        print(f"Server is ready at {host}:{port}")

    def create_message(self, type, data):
        return json.dumps({"type": type, "payload": data})

    def send_file(self, client, path, user):
        if not os.path.exists(path):
            error_msg = self.create_message('error', {'message': f"File {path} not found."})
            client.send(error_msg.encode('utf-8'))
            return

        with open(path, 'rb') as f:
            content = f.read()
            file_name = os.path.basename(path)
            server_file = os.path.join(self.server_files, file_name)

            with open(server_file, 'wb') as sf:
                sf.write(content)

        notify = self.create_message("notification", {"message": f"{user} has uploaded the file {file_name}."})
        client.send(notify.encode('utf-8'))

    def get_file(self, client, name):
        path = os.path.join(self.server_files, name)

        if not os.path.exists(path):
            error_msg = self.create_message('error', {'message': f"The file {name} is not found."})
            client.send(error_msg.encode('utf-8'))
            return

        file_data = self.create_message('file_info', {'name': name})
        client.send(file_data.encode('utf-8'))

        with open(path, 'rb') as f:
            chunk = f.read(1024)
            while chunk:
                client.send(chunk)
                chunk = f.read(1024)

    def manage_client(self, client, addr):
        username = ""
        chatroom = ""

        while True:
            try:
                msg_json = client.recv(1024).decode('utf-8')
                if not msg_json:
                    break

                msg = json.loads(msg_json)

                if msg["type"] == "connect":
                    username = msg["payload"]["name"]
                    chatroom = msg["payload"]["room"]
                    chatroom_clients = self.chatrooms.get(chatroom, [])
                    chatroom_clients.append(client)
                    self.chatrooms[chatroom] = chatroom_clients

                    ack = self.create_message("connect_ack", {"message": "You have joined the chatroom."})
                    client.send(ack.encode('utf-8'))

                    notify = self.create_message("notification", {"message": f"{username} joined the chatroom."})
                    for c in chatroom_clients:
                        if c != client:
                            c.send(notify.encode('utf-8'))

                elif msg["type"] == "message":
                    chatroom_clients = self.chatrooms.get(chatroom, [])
                    broadcast = self.create_message("message", {
                        "sender": username,
                        "room": chatroom,
                        "text": msg["payload"]["text"]
                    })

                    for c in chatroom_clients:
                        c.send(broadcast.encode('utf-8'))

                elif msg["type"] == "upload":
                    path = msg["payload"]["path"]
                    self.send_file(client, path, username)

                elif msg["type"] == "download":
                    name = msg["payload"]["name"]
                    self.get_file(client, name)

            except Exception as e:
                print(f"An error occurred: {e}")
                break

        self.clients.remove(client)
        if chatroom in self.chatrooms:
            self.chatrooms[chatroom].remove(client)
        client.close()
        print(f"Closed connection from {addr}.")

    def start(self):
        try:
            while True:
                client, address = self.server_socket.accept()
                self.clients.append(client)
                client_thread = threading.Thread(target=self.manage_client, args=(client, address))
                client_thread.start()
        except KeyboardInterrupt:
            print("Server is shutting down.")
        finally:
            self.server_socket.close()

# Usage
server = Server('127.0.0.1', 4000)
server.start()

