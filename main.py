import pygame as pg
import numpy as np
import socket, json, threading
import random

screen_dimensions = (500, 500)
screen = pg.display.set_mode(screen_dimensions)

room_code = ''.join(chr(random.randint(65, 90)) for _ in range(8))
sock = socket.socket()
sock.connect(('your-server-ip', 5555))
sock.sendall(room_code.encode())

def send_move(from_pos, to_pos):
    data = json.dumps({"from": from_pos, "to": to_pos})
    sock.sendall(data.encode())

def listen():
    while True:
        data = sock.recv(1024)
        move = json.loads(data)
        apply_move(move)  # your backend function

threading.Thread(target=listen, daemon=True).start()

game_loop = True
while game_loop:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            game_loop = False

    screen.fill(color=(234, 212, 252))
    pg.display.flip()
pg.quit()