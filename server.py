import socket
import threading

rooms = {}
_rooms_lock = threading.Lock()

def handle_client(conn, code, player_index):
    try:
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                with _rooms_lock:
                    room = rooms.get(code, [])
                if len(room) == 2:
                    other = room[1 - player_index]
                    try:
                        other.sendall(data)
                    except OSError:
                        break
            except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                print(f"Player {player_index} recv/send error: {e}")
                break
    finally:
        with _rooms_lock:
            if code in rooms:
                try:
                    rooms[code].remove(conn)
                except ValueError:
                    pass
                if not rooms[code]:
                    del rooms[code]
        try:
            conn.close()
        except OSError:
            pass
        print(f"Player {player_index} disconnected from room {code}")

def main():
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5555))
    server.listen()
    print("Server listening on port 5555")
    while True:
        conn, addr = server.accept()
        try:
            raw = b""
            while b"\n" not in raw:
                chunk = conn.recv(1024)
                if not chunk:
                    conn.close()
                    continue
                raw += chunk
            code = raw.decode().strip()
            if not code:
                try:
                    conn.close()
                except OSError:
                    pass
                continue
        except (ConnectionResetError, OSError) as e:
            print(f"Connection from {addr} failed before code: {e}")
            try:
                conn.close()
            except OSError:
                pass
            continue
        print(f"Connection from {addr}, code: {code}")
        with _rooms_lock:
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