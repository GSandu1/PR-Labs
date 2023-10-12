import socket
import threading
import json

HOST = '127.0.0.1'
PORT = 6000

def receive_messages():
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                print("Connection lost.")
                break

            message_json = json.loads(message)
            msg_type = message_json.get('type')

            if msg_type == 'notification':
                print(message_json['payload']['message'])
            elif msg_type == 'message':
                payload = message_json['payload']
                print(f"{payload['sender']}: {payload['text']}")
            elif msg_type == 'connect_ack':
                print(message_json['payload']['message'])
            else:
                print(f"Received: {message_json}")

        except Exception as e:
            print(f"Error occurred: {e}")
            break

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_socket.connect((HOST, PORT))

print(f"Connected to {HOST}:{PORT}")

name = input("Enter nickname: ").strip()
while not name:
    print("Name cannot be empty.")
    name = input("Enter nickname: ").strip()

room = input("Enter the room you want to join: ").strip()
while not room:
    print("Room cannot be empty.")
    room = input("Enter the room you want to join: ").strip()

connect_msg = {
    "type": "connect",
    "payload": {"name": name, "room": room}
}

client_socket.send(json.dumps(connect_msg).encode('utf-8'))

receive_thread = threading.Thread(target=receive_messages)
receive_thread.daemon = True
receive_thread.start()

try:
    while True:
        text = input()
        if text.lower() == 'exit':
            break

        message = {
            "type": "message",
            "payload": {"sender": name, "room": room, "text": text}
        }
        client_socket.send(json.dumps(message).encode('utf-8'))
except KeyboardInterrupt:
    print("Exiting the client.")
finally:
    client_socket.close()
