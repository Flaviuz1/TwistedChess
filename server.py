import socket, threading

rooms: dict[str, list] = {}
lock  = threading.Lock()

def handle_client(conn, code, idx):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            with lock:
                room = rooms.get(code, [])
            if len(room) == 2:
                other = room[1 - idx]
                try:
                    other.sendall(data)
                except OSError:
                    break
        except OSError:
            break
    print(f"Player {idx} left room {code}")
    with lock:
        if code in rooms:
            try: rooms[code].remove(conn)
            except ValueError: pass
            if not rooms[code]:
                del rooms[code]
    try: conn.close()
    except OSError: pass

def main():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', 5555))
    srv.listen()
    print("Server listening on :5555")
    while True:
        conn, addr = srv.accept()
        try:
            raw = b""
            while b"\n" not in raw:
                chunk = conn.recv(1024)
                if not chunk: raise ConnectionError()
                raw += chunk
            code = raw.decode().strip()
            if not code: raise ValueError("empty code")
        except Exception as e:
            print(f"Bad connection from {addr}: {e}")
            try: conn.close()
            except: pass
            continue

        with lock:
            if code not in rooms:
                rooms[code] = [conn]
                idx = 0
                conn.sendall(b'0\n')
                print(f"[{code}] created by {addr} — waiting...")
            else:
                rooms[code].append(conn)
                idx = 1
                conn.sendall(b'1\n')
                print(f"[{code}] full — game on!")

        threading.Thread(target=handle_client, args=(conn, code, idx), daemon=True).start()

if __name__ == "__main__":
    main()