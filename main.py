import pygame as pg
import numpy as np
import socket, json, threading
import random
import classes
import server

player_id = 1

# CONSTANTS
screen_dimension = 400 * 2
screen = pg.display.set_mode((screen_dimension, screen_dimension))
tile_size = 44.8718 * 2
sprite_size = 35.8974 * 2
offset = 4.4872 * 2
beginning_offset = 27.2436 * 2
sprite_slide = 22.4359 * 2
sprites = {
    "Pw": pg.transform.scale(pg.image.load("Assets/PawnWhite.png"),   (sprite_size, sprite_size)),
    "Pb": pg.transform.scale(pg.image.load("Assets/PawnBlack.png"),   (sprite_size, sprite_size)),
    "Nw": pg.transform.scale(pg.image.load("Assets/KnightWhite.png"), (sprite_size, sprite_size)),
    "Nb": pg.transform.scale(pg.image.load("Assets/KnightBlack.png"), (sprite_size, sprite_size)),
    "Bw": pg.transform.scale(pg.image.load("Assets/BishopWhite.png"), (sprite_size, sprite_size)),
    "Bb": pg.transform.scale(pg.image.load("Assets/BishopBlack.png"), (sprite_size, sprite_size)),
    "Rw": pg.transform.scale(pg.image.load("Assets/RookWhite.png"),   (sprite_size, sprite_size)),
    "Rb": pg.transform.scale(pg.image.load("Assets/RookBlack.png"),   (sprite_size, sprite_size)),
    "Qw": pg.transform.scale(pg.image.load("Assets/QueenWhite.png"),  (sprite_size, sprite_size)),
    "Qb": pg.transform.scale(pg.image.load("Assets/QueenBlack.png"),  (sprite_size, sprite_size)),
    "Kw": pg.transform.scale(pg.image.load("Assets/KingWhite.png"),   (sprite_size, sprite_size)),
    "Kb": pg.transform.scale(pg.image.load("Assets/KingBlack.png"),   (sprite_size, sprite_size)),
    "Board": pg.transform.scale(pg.image.load("Assets/ChessBoard.png"),   (screen_dimension, screen_dimension))}

# MULTIPLAYER
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
sock.sendall(room_code.encode())
player_id = int(sock.recv(1024).decode())
my_color = 'white' if player_id == 0 else 'black'

moves_this_round = 0
def apply_move(move):
    global moves_this_round
    
    from_row, from_col = move["from"]
    to_row, to_col = move["to"]
    
    piece = board.grid[from_row][from_col]
    board.grid[to_row][to_col] = piece
    board.grid[from_row][from_col] = "   "
    
    moves_this_round += 1
    if moves_this_round >= 2:
        moves_this_round = 0
        board.rotate_board()


board = classes.Board()
def draw_pieces(visual_row, visual_col, board_row, board_col):
    piece = board.grid[board_row][board_col]
    if piece.strip():
        key = piece[0] + piece[2]
        sprite = sprites[key]
        x = beginning_offset + visual_col * (tile_size + offset) - sprite_slide + 8
        y = beginning_offset + visual_row * (tile_size + offset) - sprite_slide + 10
        screen.blit(sprite, (x, y))

def click_piece(mx, my):
    col = int((mx - beginning_offset + sprite_slide - 8) / (tile_size + offset))
    row = int((my - beginning_offset + sprite_slide - 10) / (tile_size + offset))
    if 0 <= row < 8 and 0 <= col < 8:
        piece = board.grid[row][col]
        if piece.strip():
            print(f"Clicked piece: {piece} at ({row}, {col})")
        else:
            print(f"Empty square at ({row}, {col})")
    return (col, row)

game_loop = True
while game_loop:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            game_loop = False
        if event.type == pg.MOUSEBUTTONDOWN:
            mx, my = pg.mouse.get_pos()
            click_piece(mx, my)

    screen.fill(color=(0,0,0))
    screen.blit(sprites["Board"], (0,0))
    for visual_row in range(8):
        for visual_col in range(8):
            board_row = None
            board_col = None
            if my_color == 'white':
                board_row, board_col = visual_row, visual_col
            else:
                board_row, board_col = 7 - visual_row, 7 - visual_col
            draw_pieces(visual_row, visual_col, board_row, board_col)

    pg.display.flip()
pg.quit()