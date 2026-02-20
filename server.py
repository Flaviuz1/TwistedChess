import socket, threading, json

rooms = {}  # code -> [conn1, conn2]

def handle_client(conn, code, player_id):
    room = rooms[code]
    other = room[1 - player_id]
    while True:
        data = conn.recv(1024)
        if not data: break
        other.sendall(data)  # just relay to the other player

def main():
    server = socket.socket()
    server.bind(('0.0.0.0', 5555))
    server.listen()
    while True:
        conn, addr = server.accept()
        code = conn.recv(1024).decode()
        if code not in rooms:
            rooms[code] = [conn]
        else:
            rooms[code].append(conn)
            for i, c in enumerate(rooms[code]):
                threading.Thread(target=handle_client, args=(c, code, i)).start()