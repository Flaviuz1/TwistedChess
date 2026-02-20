import socket, threading, json

rooms = {}

def handle_client(conn, code, player_index):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            room = rooms.get(code, [])
            if len(room) == 2:
                other = room[1 - player_index]
                other.sendall(data)
        except:
            break
    print(f"Player {player_index} disconnected from room {code}")

def main():
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5555))
    server.listen()
    print("Server listening on port 5555")
    while True:
        conn, addr = server.accept()
        raw  = b""
        while b"\n" not in raw:
            raw += conn.recv(1024)
        code = raw.decode().strip()
        print(f"Connection from {addr}, code: {code}")
        if code not in rooms:
            rooms[code] = [conn]
            conn.sendall(b'0\n')
            print(f"Room {code} created — waiting for second player")
        else:
            rooms[code].append(conn)
            conn.sendall(b'1\n')
            print(f"Room {code} full — game starting!")
        player_index = len(rooms[code]) - 1
        threading.Thread(target=handle_client, args=(conn, code, player_index), daemon=True).start()

if __name__ == "__main__":
    main()