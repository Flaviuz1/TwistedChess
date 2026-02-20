import pygame as pg
import socket
import json
import threading
import random
import os

import classes

pg.init()

# ── CONSTANTS ────────────────────────────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.join(_BASE, "Assets")

def _asset(path: str):
    return os.path.join(_ASSETS, path)

screen_w = 400 * 2 + 200
screen_h = 400 * 2
screen = pg.display.set_mode((screen_w, screen_h))
tile_size    = 44.8718 * 2
sprite_size  = 35.8974 * 2
offset       = 4.4872  * 2
beg_offset   = 27.2436 * 2
sprite_slide = 22.4359 * 2
panel_x      = 820
panel_cx     = 900

sprites = {
    "Pw": pg.transform.scale(pg.image.load(_asset("PawnWhite.png")),    (sprite_size, sprite_size)),
    "Pb": pg.transform.scale(pg.image.load(_asset("PawnBlack.png")),    (sprite_size, sprite_size)),
    "Nw": pg.transform.scale(pg.image.load(_asset("KnightWhite.png")),  (sprite_size, sprite_size)),
    "Nb": pg.transform.scale(pg.image.load(_asset("KnightBlack.png")),  (sprite_size, sprite_size)),
    "Bw": pg.transform.scale(pg.image.load(_asset("BishopWhite.png")),  (sprite_size, sprite_size)),
    "Bb": pg.transform.scale(pg.image.load(_asset("BishopBlack.png")),  (sprite_size, sprite_size)),
    "Rw": pg.transform.scale(pg.image.load(_asset("RookWhite.png")),    (sprite_size, sprite_size)),
    "Rb": pg.transform.scale(pg.image.load(_asset("RookBlack.png")),    (sprite_size, sprite_size)),
    "Qw": pg.transform.scale(pg.image.load(_asset("QueenWhite.png")),   (sprite_size, sprite_size)),
    "Qb": pg.transform.scale(pg.image.load(_asset("QueenBlack.png")),   (sprite_size, sprite_size)),
    "Kw": pg.transform.scale(pg.image.load(_asset("KingWhite.png")),    (sprite_size, sprite_size)),
    "Kb": pg.transform.scale(pg.image.load(_asset("KingBlack.png")),    (sprite_size, sprite_size)),
    "Board": pg.transform.scale(pg.image.load(_asset("ChessBoard.png")), (screen_h, screen_h)),
}

# ── UI STATE ──────────────────────────────────────────────────────────────────
code_input   = ""
input_active = False
input_rect   = pg.Rect(820, 450, 160, 36)
btn_rect     = pg.Rect(820, 500, 160, 36)
font_ui      = pg.font.SysFont("Consolas", 18)
font_small   = pg.font.SysFont("Consolas", 13)

# ── GAME STATE ────────────────────────────────────────────────────────────────
board            = classes.Board()
moves_this_round = 0
selected         = None

# ── NETWORK STATE — nothing connects at startup ───────────────────────────────
room_code = ''.join(chr(random.randint(65, 90)) for _ in range(8))
sock      = socket.socket()
player_id = None
my_color  = 'w'   # placeholder until connected
my_turn   = False  # nobody can move until connected
connected = False

# ── NETWORKING ────────────────────────────────────────────────────────────────
def apply_move(move):
    global moves_this_round, my_turn
    try:
        fr, fc = move["from"][0], move["from"][1]
        tr, tc = move["to"][0], move["to"][1]
    except (KeyError, TypeError, IndexError):
        return
    if not (0 <= fr < 8 and 0 <= fc < 8 and 0 <= tr < 8 and 0 <= tc < 8):
        return
    board.move(fr, fc, tr, tc)
    moves_this_round += 1
    if moves_this_round >= 2:
        moves_this_round = 0
        board.rotate_board()
    my_turn = not my_turn

def send_move(from_pos, to_pos):
    if not connected:
        return
    try:
        data = json.dumps({"from": list(from_pos), "to": list(to_pos)})
        sock.sendall((data + "\n").encode())
    except Exception as e:
        print(f"Send error: {e}")

def listen():
    global connected
    buffer = b""
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                break
            buffer += data
            while b"\n" in buffer:
                line_b, buffer = buffer.split(b"\n", 1)
                line = line_b.decode("utf-8", errors="replace").strip()
                if line:
                    try:
                        apply_move(json.loads(line))
                    except (json.JSONDecodeError, TypeError):
                        pass
        except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
            print(f"Listen error: {e}")
            break
    connected = False

def connect_with_code(code):
    global player_id, my_color, connected, my_turn, sock
    try:
        sock.connect(('localhost', 5555))
        sock.sendall((code + "\n").encode())
        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(1024)
            if not chunk:
                raise ConnectionError("Server closed connection")
            buf += chunk
        player_id = int(buf.decode().strip())
        my_color  = 'w' if player_id == 0 else 'b'
        my_turn   = (player_id == 0)  # white moves first
        connected = True
        threading.Thread(target=listen, daemon=True).start()
        print(f"Connected as {'WHITE' if player_id == 0 else 'BLACK'}, my_turn={my_turn}")
    except Exception as e:
        print(f"Connection failed: {e}")
        try:
            sock.close()
        except OSError:
            pass
        sock = socket.socket()

# ── DRAWING ───────────────────────────────────────────────────────────────────
def draw_pieces():
    for visual_row in range(8):
        for visual_col in range(8):
            if my_color == 'w':
                board_row, board_col = visual_row, visual_col
            else:
                board_row, board_col = 7 - visual_row, 7 - visual_col

            # draw highlight under piece
            if selected == (board_row, board_col):
                sx = beg_offset + visual_col * (tile_size + offset)
                sy = beg_offset + visual_row * (tile_size + offset)
                s = pg.Surface((int(tile_size), int(tile_size)), pg.SRCALPHA)
                s.fill((255, 255, 0, 90))
                screen.blit(s, (sx, sy))

            piece = board.get(board_row, board_col)
            if piece:
                key    = piece.type + piece.color
                sprite = sprites[key]
                x = beg_offset + visual_col * (tile_size + offset) - sprite_slide + 8
                y = beg_offset + visual_row * (tile_size + offset) - sprite_slide + 8
                screen.blit(sprite, (x, y))

def draw_arrow():
    cx, cy = panel_cx, 200
    size   = 40
    rot    = board.rotation
    directions = {
        0: [(cx,cy-size),(cx-20,cy+10),(cx-8,cy+10),(cx-8,cy+size),(cx+8,cy+size),(cx+8,cy+10),(cx+20,cy+10)],
        1: [(cx+size,cy),(cx-10,cy-20),(cx-10,cy-8),(cx-size,cy-8),(cx-size,cy+8),(cx-10,cy+8),(cx-10,cy+20)],
        2: [(cx,cy+size),(cx-20,cy-10),(cx-8,cy-10),(cx-8,cy-size),(cx+8,cy-size),(cx+8,cy-10),(cx+20,cy-10)],
        3: [(cx-size,cy),(cx+10,cy-20),(cx+10,cy-8),(cx+size,cy-8),(cx+size,cy+8),(cx+10,cy+8),(cx+10,cy+20)],
    }
    pg.draw.polygon(screen, (220, 180, 80),  directions[rot])
    pg.draw.polygon(screen, (255, 220, 100), directions[rot], 2)
    lbl = font_small.render("PAWN DIRECTION", True, (180, 180, 180))
    screen.blit(lbl, (cx - lbl.get_width()//2, cy + size + 12))

def draw_ui():
    # turn indicator
    turn_text = ("YOUR TURN" if my_turn else "WAITING...") if connected else "NOT CONNECTED"
    turn_col  = (100, 220, 100) if my_turn else (180, 100, 100)
    screen.blit(font_small.render(turn_text, True, turn_col), (panel_x, 290))

    # your code
    screen.blit(font_small.render("YOUR CODE", True, (100, 100, 100)), (panel_x, 320))
    screen.blit(font_ui.render(room_code, True, (100, 180, 100)),      (panel_x, 338))

    pg.draw.line(screen, (60, 60, 60), (810, 410), (990, 410), 1)

    # join label + input
    screen.blit(font_small.render("JOIN WITH CODE", True, (150, 150, 150)), (panel_x, 420))
    border_col = (220, 180, 80) if input_active else (60, 60, 60)
    pg.draw.rect(screen, (30, 30, 30), input_rect)
    pg.draw.rect(screen, border_col,   input_rect, 2)
    text_surf = font_ui.render(code_input, True, (220, 220, 220))
    screen.blit(text_surf, (input_rect.x + 8, input_rect.y + 8))

    # blinking cursor
    if input_active and (pg.time.get_ticks() // 500) % 2 == 0:
        cx = input_rect.x + 8 + text_surf.get_width() + 2
        pg.draw.line(screen, (220,220,220), (cx, input_rect.y+6), (cx, input_rect.y+28), 2)

    # connect button
    btn_col = (20, 60, 20) if connected else (60, 50, 20)
    pg.draw.rect(screen, btn_col,        btn_rect)
    pg.draw.rect(screen, (220, 180, 80), btn_rect, 2)
    btn_text = font_ui.render("CONNECTED" if connected else "CONNECT", True, (220, 180, 80))
    screen.blit(btn_text, (btn_rect.x + btn_rect.width//2 - btn_text.get_width()//2, btn_rect.y + 8))

    # color indicator once connected
    if connected:
        col_txt = "PLAYING AS WHITE" if my_color == 'w' else "PLAYING AS BLACK"
        screen.blit(font_small.render(col_txt, True, (180,180,100)), (panel_x, 548))

# ── INPUT ─────────────────────────────────────────────────────────────────────
def screen_to_board(mx, my):
    col = int((mx - beg_offset + sprite_slide - 8)  / (tile_size + offset))
    row = int((my - beg_offset + sprite_slide - 10) / (tile_size + offset))
    if not (0 <= row < 8 and 0 <= col < 8):
        return None
    if my_color == 'b':
        return (7 - row, 7 - col)
    return (row, col)

def handle_click(mx, my):
    global selected
    if not connected or not my_turn:
        return
    pos = screen_to_board(mx, my)
    if pos is None:
        selected = None
        return
    r, c   = pos
    piece  = board.get(r, c)

    if selected is None:
        if piece and piece.color == my_color:
            selected = (r, c)
    else:
        if (r, c) == selected:
            selected = None
        elif piece and piece.color == my_color:
            selected = (r, c)
        else:
            from_pos = selected
            move     = {"from": list(from_pos), "to": [r, c]}
            apply_move(move)          # apply locally
            send_move(from_pos, (r,c)) # send to opponent via server
            selected = None

# ── GAME LOOP ─────────────────────────────────────────────────────────────────
clock     = pg.time.Clock()
game_loop = True
while game_loop:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            game_loop = False

        if event.type == pg.MOUSEBUTTONDOWN:
            input_active = input_rect.collidepoint(event.pos)
            if btn_rect.collidepoint(event.pos):
                if not connected and len(code_input) == 8:
                    connect_with_code(code_input)
            else:
                handle_click(event.pos[0], event.pos[1])

        if event.type == pg.KEYDOWN and input_active:
            if event.key == pg.K_BACKSPACE:
                code_input = code_input[:-1]
            elif event.key == pg.K_RETURN:
                if not connected and len(code_input) == 8:
                    connect_with_code(code_input)
            elif len(code_input) < 8 and event.unicode.isalpha():
                code_input += event.unicode.upper()

    screen.fill((20, 20, 20))
    screen.blit(sprites["Board"], (0, 0))
    draw_pieces()
    draw_arrow()
    draw_ui()
    pg.display.flip()
    clock.tick(60)

try:
    if sock:
        sock.close()
except (OSError, NameError):
    pass
pg.quit()