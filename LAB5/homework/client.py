import socket
import threading
import uuid
import json
import os

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_id = str(uuid.uuid4())
        self.client_folder = os.path.join('Downloads', self.client_id)
        os.makedirs(self.client_folder, exist_ok=True)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")

    def get_messages(self):
        file = None
        receiving_file = False
        while True:
            try:
                msg = self.client_socket.recv(1024)
                if not msg:
                    print("Lost connection.")
                    break

                if receiving_file:
                    with open(os.path.join(self.client_folder, file), 'ab') as f:
                        f.write(msg)
                        while True:
                            self.client_socket.settimeout(0.5)
                            try:
                                chunk = self.client_socket.recv(1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                            except socket.timeout:
                                break

                    print(f"File {file} downloaded to {os.path.join(self.client_folder, file)}.")
                    file = None
                    receiving_file = False
                    self.client_socket.settimeout(None)
                    continue

                msg_str = msg.decode('utf-8', errors='ignore')

                if msg_str.strip().startswith('{') and msg_str.strip().endswith('}'):
                    msg_json = json.loads(msg_str)
                    type = msg_json.get('type')

                    if type == 'file_info':
                        file = msg_json['payload']['name']
                        receiving_file = True
                    elif type == 'notification':
                        print(msg_json['payload']['message'])
                    elif type == 'message':
                        payload = msg_json['payload']
                        print(f"{payload['sender']}: {payload['text']}")
                    elif type == 'connect_ack':
                        print(msg_json['payload']['message'])
                    elif type == 'error':
                        print(msg_json['payload']['message'])

            except Exception as e:
                print(f"An error occurred: {e}")
                break

    def send_message(self, text, username, chatroom):
        try:
            if text.lower().startswith('upload:'):
                _, path = text.split(':', 1)
                msg = {
                    "type": "upload",
                    "payload": {"path": path.strip()}
                }
            elif text.lower().startswith('download:'):
                _, name = text.split(':', 1)
                msg = {
                    "type": "download",
                    "payload": {"name": name.strip()}
                }
            else:
                msg = {
                    "type": "message",
                    "payload": {"sender": username, "room": chatroom, "text": text}
                }

            self.client_socket.send(json.dumps(msg).encode('utf-8'))
        except Exception as e:
            print(f"An error occurred while sending the message: {e}")

    def start(self, username, chatroom):
        init_msg = {
            "type": "connect",
            "payload": {"name": username, "room": chatroom}
        }
        self.client_socket.send(json.dumps(init_msg).encode('utf-8'))

        msg_thread = threading.Thread(target=self.get_messages)
        msg_thread.daemon = True
        msg_thread.start()

        try:
            while True:
                text = input()
                if text.lower() == 'exit':
                    break
                self.send_message(text, username, chatroom)
        except KeyboardInterrupt:
            print("\nClient is exiting.")
        finally:
            self.client_socket.close()

# Usage
client = Client('127.0.0.1', 4000)
username = input("name: ").strip()
chatroom = input("room: ").strip()
client.start(username, chatroom)
