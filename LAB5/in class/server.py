import socket
import threading
import json

HOST = '127.0.0.1'
PORT = 6000

clients = []
rooms = {}

def format_message(msg_type, payload):
    return json.dumps({"type": msg_type, "payload": payload})

def handle_client(client_socket, client_address):
    global clients, rooms
    client_name = ""
    client_room = ""

    while True:
        try:
            message_json = client_socket.recv(1024).decode('utf-8')
            if not message_json:
                break

            message_data = json.loads(message_json)
            print(f"Received: {message_json}")

            if message_data["type"] == "connect":
                client_name = message_data["payload"]["name"]
                client_room = message_data["payload"]["room"]
                clients_in_room = rooms.get(client_room, [])
                clients_in_room.append(client_socket)
                rooms[client_room] = clients_in_room

                ack_message = format_message("connect_ack", {"message": "Connected to the room."})
                client_socket.send(ack_message.encode('utf-8'))
                print(f"{client_name} connected to room {client_room}")  # Print client connections to the terminal

                notification = format_message("notification", {"message": f"{client_name} has joined the room."})
                for client in clients_in_room:
                    if client != client_socket:
                        client.send(notification.encode('utf-8'))

            elif message_data["type"] == "message":
                clients_in_room = rooms.get(client_room, [])
                broadcast_message = format_message("message", {
                    "sender": client_name,
                    "room": client_room,
                    "text": message_data["payload"]["text"]
                })
                print(f"Message in {client_room} from {client_name}: {message_data['payload']['text']}")
                for client in clients_in_room:
                    client.send(broadcast_message.encode('utf-8'))

        except json.JSONDecodeError:
            print(f"Received invalid JSON data from {client_address}. Continuing...")

    clients.remove(client_socket)
    if client_room in rooms:
        rooms[client_room].remove(client_socket)
    client_socket.close()
    print(f"Connection from {client_address} closed.")

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server is listening on {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            clients.append(client_socket)
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down the server.")
    finally:
        server_socket.close()
