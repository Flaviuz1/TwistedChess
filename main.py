import pygame as pg
import json
import threading
import random
import os
import math
import sys
import classes

# WebSocket server URL (wss:// for HTTPS, ws:// for localhost)
# Set via env TWISTEDCHESS_SERVER or change default for Render deployment
SERVER_URL = os.environ.get("TWISTEDCHESS_SERVER", "wss://twistedchess.onrender.com/ws")

pg.init()

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    _BASE = sys._MEIPASS  # type: ignore[attr-defined]
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.join(_BASE, "Assets")

def _a(f):
    return os.path.join(_ASSETS, f)

screen_w = 400 * 2 + 400
screen_h = 400 * 2
screen = pg.display.set_mode((screen_w, screen_h))
tile_size = 44.8718 * 2
sprite_size = 35.8974 * 2
offset = 4.4872 * 2
beg_offset = 27.2436 * 2
sprite_slide = 22.4359 * 2
panel_x = 820
panel_cx = 900

MOVE_ANIM_MS = 240
ROT_ANIM_MS = 220

def scale(path):
    return pg.transform.scale(pg.image.load(_a(path)), (sprite_size, sprite_size))

sprites = {
    "Pw": scale("PawnWhite.png"), "Pb": scale("PawnBlack.png"),
    "Nw": scale("KnightWhite.png"), "Nb": scale("KnightBlack.png"),
    "Bw": scale("BishopWhite.png"), "Bb": scale("BishopBlack.png"),
    "Rw": scale("RookWhite.png"), "Rb": scale("RookBlack.png"),
    "Qw": scale("QueenWhite.png"), "Qb": scale("QueenBlack.png"),
    "Kw": scale("KingWhite.png"), "Kb": scale("KingBlack.png"),
    "Board": pg.transform.scale(pg.image.load(_a("ChessBoard.png")), (screen_h, screen_h)),
}

font_ui = pg.font.SysFont("Consolas", 18)
font_small = pg.font.SysFont("Consolas", 13)
font_big = pg.font.SysFont("Consolas", 22, bold=True)

# ── UI RECTS ───────────────────────────────────────────────────────────────
btn_create = pg.Rect(820, 310, 160, 34)
input_rect = pg.Rect(820, 410, 160, 34)
btn_join = pg.Rect(820, 454, 160, 34)

# ── STATE ─────────────────────────────────────────────────────────────────────
board = classes.Board()
moves_this_round = 0
selected = None
legal_moves: list[tuple[int, int]] = []
last_move = None
game_over = None  # None | "won" | "lost"

room_code = "".join(chr(random.randint(65, 90)) for _ in range(4))
ws = None  # WebSocket connection
player_id = None
my_color = "w"
my_turn = False
connected = False
input_active = False
code_input = ""
status_msg = ""

# ── ANIMATIONS ───────────────────────────────────────────────────────────────
move_anim = None  # { "piece_key", "from_vr","from_vc","to_vr","to_vc", "start_ms" }
rotation_anim = None  # { "start_rot", "start_ms" }  # animates 0..90 then we call rotate_board

# ── NETWORKING ───────────────────────────────────────────────────────────────
def apply_move(move_dict):
    global moves_this_round, my_turn, last_move, game_over
    try:
        fr, fc = move_dict["from"][0], move_dict["from"][1]
        tr, tc = move_dict["to"][0], move_dict["to"][1]
    except (KeyError, TypeError, IndexError):
        return
    if not (0 <= fr < 8 and 0 <= fc < 8 and 0 <= tr < 8 and 0 <= tc < 8):
        return
    promo = move_dict.get("promotion")
    board.move(fr, fc, tr, tc, promotion=promo)
    last_move = (fr, fc, tr, tc)
    moves_this_round += 1
    if moves_this_round >= 2:
        moves_this_round = 0
        rotation_anim_start()
    my_turn = not my_turn
    opp = "b" if my_color == "w" else "w"
    if board.is_checkmate(opp):
        game_over = "won"
    elif board.is_checkmate(my_color):
        game_over = "lost"

def send_move(from_pos, to_pos, promotion=None):
    if not connected or ws is None:
        return
    try:
        payload = {"from": list(from_pos), "to": list(to_pos)}
        if promotion:
            payload["promotion"] = promotion
        ws.send(json.dumps(payload))
    except Exception as e:
        print(f"Send error: {e}")

def listen():
    global connected, status_msg
    while True:
        try:
            msg = ws.recv() # type: ignore[attr-defined]
            if not msg:
                break
            line = msg.strip()
            if line:
                try:
                    apply_move(json.loads(line))
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception as e:
            if "closed" not in str(e).lower():
                print(f"Listen error: {e}")
            break
    connected = False
    status_msg = "Disconnected"

def _do_connect(code):
    global player_id, my_color, connected, my_turn, status_msg, ws
    conn = None
    try:
        import websocket
        conn = websocket.create_connection(SERVER_URL)
        conn.send(code)
        resp = conn.recv()
        player_id = int(resp.strip())
        my_color = "w" if player_id == 0 else "b"
        my_turn = player_id == 0
        connected = True
        ws = conn
        status_msg = f"Connected as {'WHITE' if player_id == 0 else 'BLACK'}"
        threading.Thread(target=listen, daemon=True).start()
        print(status_msg)
    except Exception as e:
        status_msg = f"Failed: {e}"
        print(status_msg)
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        ws = None

def create_room():
    threading.Thread(target=_do_connect, args=(room_code,), daemon=True).start()

def join_room():
    if len(code_input) == 8:
        threading.Thread(target=_do_connect, args=(code_input,), daemon=True).start()

def rotation_anim_start():
    global rotation_anim
    rotation_anim = {"start_rot": board.rotation, "start_ms": pg.time.get_ticks()}

def rotation_anim_tick():
    global rotation_anim, last_move
    if rotation_anim is None:
        return
    elapsed = pg.time.get_ticks() - rotation_anim["start_ms"]
    if elapsed >= ROT_ANIM_MS:
        board.rotate_board()
        if last_move:
            fr, fc, tr, tc = last_move
            last_move = (fc, 7 - fr, tc, 7 - tr)
        rotation_anim = None
        return
    rotation_anim["progress"] = elapsed / ROT_ANIM_MS  # type: ignore[attr-defined]

# ── BOARD SURFACE (for rotation) ──────────────────────────────────────────────
_board_surf = pg.Surface((screen_h, screen_h))

def _tile_rect(vr, vc):
    """Visual pixel rect for tile (vr, vc) - aligns with board squares."""
    x = beg_offset + vc * (tile_size + offset) - sprite_slide
    y = beg_offset + vr * (tile_size + offset) - sprite_slide
    return (x, y, int(tile_size), int(tile_size))

def _piece_center(vr, vc):
    cx = beg_offset + vc * (tile_size + offset) + tile_size / 2 - sprite_slide
    cy = beg_offset + vr * (tile_size + offset) + tile_size / 2 - sprite_slide
    return (cx, cy)

def draw_board_to_surface(surf, rotation_angle: float = 0):
    """Draw board + highlights + pieces onto surf. rotation_angle in degrees for anim."""
    surf.blit(sprites["Board"], (0, 0))
    for vr in range(8):
        for vc in range(8):
            br, bc = (vr, vc) if my_color == "w" else (7 - vr, 7 - vc)
            rx, ry, rw, rh = _tile_rect(vr, vc)

            if last_move and (br, bc) in ((last_move[0], last_move[1]), (last_move[2], last_move[3])):
                hl = pg.Surface((rw, rh), pg.SRCALPHA)
                hl.fill((255, 140, 0, 70))
                surf.blit(hl, (rx, ry))

            if selected == (br, bc):
                hl = pg.Surface((rw, rh), pg.SRCALPHA)
                hl.fill((255, 220, 50, 120))
                surf.blit(hl, (rx, ry))

            piece = board.get(br, bc)
            skip = move_anim and (
                (move_anim.get("piece_br") == br and move_anim.get("piece_bc") == bc)
                or (move_anim.get("to_br") == br and move_anim.get("to_bc") == bc)
            )
            if piece and not skip:
                spr = sprites[piece.type + piece.color]
                cx, cy = _piece_center(vr, vc)
                x, y = cx - sprite_size / 2, cy - sprite_size / 2
                surf.blit(spr, (x, y))

    if move_anim:
        t = pg.time.get_ticks() - move_anim["start_ms"]
        if t >= MOVE_ANIM_MS:
            move_anim_finish()
        else:
            progress = t / MOVE_ANIM_MS
            x1, y1 = _piece_center(move_anim["from_vr"], move_anim["from_vc"])
            x2, y2 = _piece_center(move_anim["to_vr"], move_anim["to_vc"])
            x = x1 + (x2 - x1) * progress
            y = y1 + (y2 - y1) * progress
            scale_fac = 1.0
            if progress < 0.5:
                scale_fac = 1.0 + 0.35 * (progress * 2)
            else:
                scale_fac = 1.35 - 0.35 * ((progress - 0.5) * 2)
            spr = sprites[move_anim["piece_key"]]
            w, h = int(sprite_size * scale_fac), int(sprite_size * scale_fac)
            scaled = pg.transform.smoothscale(spr, (w, h))
            surf.blit(scaled, (x - w / 2, y - h / 2))

    if rotation_angle != 0:
        rotated = pg.transform.rotate(surf, -rotation_angle)
        rect = rotated.get_rect(center=(screen_h / 2, screen_h / 2))
        return rotated, rect
    return surf, pg.Rect(0, 0, screen_h, screen_h)

def move_anim_finish():
    global move_anim
    move_anim = None

def draw_pieces_and_board():
    rotation_anim_tick()
    rot_angle = 0.0
    if rotation_anim is not None and "progress" in rotation_anim:
        rot_angle = rotation_anim["progress"] * 90
    _board_surf.fill((0, 0, 0))
    result, rect = draw_board_to_surface(_board_surf, rot_angle)
    if isinstance(result, pg.Surface) and result != _board_surf:
        screen.blit(result, rect)
    else:
        screen.blit(_board_surf, (0, 0))

def _rotate_point(cx, cy, x, y, deg):
    rad = math.radians(deg)
    cos, sin = math.cos(rad), math.sin(rad)
    dx, dy = x - cx, y - cy
    return (cx + dx * cos - dy * sin, cy + dx * sin + dy * cos)

def draw_arrow():
    cx, cy = panel_cx, 130
    sz = 35
    angle_deg = board.rotation * 90
    if rotation_anim is not None and "progress" in rotation_anim:
        angle_deg += rotation_anim["progress"] * 90
    # Base arrow pointing up (direction 0)
    base = [(cx, cy - sz), (cx - 18, cy + 8), (cx - 7, cy + 8), (cx - 7, cy + sz), (cx + 7, cy + sz), (cx + 7, cy + 8), (cx + 18, cy + 8)]
    dirs = [_rotate_point(cx, cy, x, y, angle_deg) for x, y in base]
    pg.draw.polygon(screen, (220, 180, 80), dirs)
    pg.draw.polygon(screen, (255, 220, 100), dirs, 2)
    lbl = font_small.render("PAWN DIRECTION", True, (160, 160, 160))
    screen.blit(lbl, (cx - lbl.get_width() // 2, cy + sz + 8))

def draw_btn(rect, label, active=False, green=False):
    col = (20, 60, 20) if green else ((60, 50, 20) if active else (35, 35, 35))
    pg.draw.rect(screen, col, rect)
    pg.draw.rect(screen, (220, 180, 80) if active or green else (70, 70, 70), rect, 2)
    t = font_small.render(label, True, (220, 180, 80) if active or green else (140, 140, 140))
    screen.blit(t, (rect.x + rect.w // 2 - t.get_width() // 2, rect.y + rect.h // 2 - t.get_height() // 2))

def draw_ui():
    screen.blit(font_small.render("YOUR ROOM CODE", True, (100, 100, 100)), (panel_x, 253))
    screen.blit(font_small.render("(Host: click CREATE ROOM \nto play as White)", True, (90, 90, 90)), (panel_x, 268))
    screen.blit(font_big.render(room_code, True, (100, 200, 100)), (panel_x, 226))
    draw_btn(btn_create, "CREATE ROOM", active=not connected, green=connected and player_id == 0)

    pg.draw.line(screen, (55, 55, 55), (812, 358), (992, 358), 1)

    screen.blit(font_small.render("JOIN WITH CODE", True, (100, 100, 100)), (panel_x, 368))
    border = (220, 180, 80) if input_active else (60, 60, 60)
    pg.draw.rect(screen, (25, 25, 25), input_rect)
    pg.draw.rect(screen, border, input_rect, 2)
    ts = font_ui.render(
        code_input + ("_" if input_active and (pg.time.get_ticks() // 500) % 2 == 0 else " "),
        True, (220, 220, 220),
    )
    screen.blit(ts, (input_rect.x + 6, input_rect.y + 7))

    draw_btn(btn_join, "JOIN ROOM", active=len(code_input) == 8 and not connected, green=connected and player_id == 1)

    pg.draw.line(screen, (55, 55, 55), (812, 498), (992, 498), 1)

    if status_msg:
        screen.blit(font_small.render(status_msg, True, (160, 160, 100)), (panel_x, 508))

    if game_over:
        msg = "You won by checkmate!" if game_over == "won" else "Checkmate. You lost."
        col = (100, 220, 100) if game_over == "won" else (220, 100, 100)
        screen.blit(font_big.render(msg, True, col), (panel_x, 518))
    elif connected:
        color_str = "WHITE" if my_color == "w" else "BLACK"
        turn_str = "YOUR TURN" if my_turn else "WAITING..."
        turn_col = (100, 220, 100) if my_turn else (200, 100, 100)
        screen.blit(font_small.render(f"Playing as {color_str}", True, (160, 160, 160)), (panel_x, 528))
        screen.blit(font_small.render(turn_str, True, turn_col), (panel_x, 548))
    else:
        screen.blit(font_small.render("Not connected", True, (150, 80, 80)), (panel_x, 528))

# ── INPUT ─────────────────────────────────────────────────────────────────────
def screen_to_board(mx, my):
    col = int((mx - beg_offset + sprite_slide - 8) / (tile_size + offset))
    row = int((my - beg_offset + sprite_slide - 10) / (tile_size + offset))
    if not (0 <= row < 8 and 0 <= col < 8):
        return None
    return (7 - row, 7 - col) if my_color == "b" else (row, col)

def board_to_visual(br, bc):
    if my_color == "w":
        return (br, bc)
    return (7 - br, 7 - bc)

def handle_click(mx, my):
    global selected, legal_moves, move_anim
    if not connected or not my_turn or game_over:
        return
    pos = screen_to_board(mx, my)
    if pos is None:
        selected = None
        legal_moves = []
        return
    r, c = pos
    piece = board.get(r, c)

    if selected is None:
        if piece and piece.color == my_color:
            selected = (r, c)
            legal_moves = board.get_legal_moves(r, c)
    else:
        if (r, c) == selected:
            selected = None
            legal_moves = []
        elif piece and piece.color == my_color:
            selected = (r, c)
            legal_moves = board.get_legal_moves(r, c)
        elif (r, c) in legal_moves:
            fr, fc = selected # type: ignore[attr-defined]
            piece_at = board.get(fr, fc)
            if not piece_at:
                selected = None
                legal_moves = []
                return
            promo = None
            if piece_at.type == "P" and board._is_promotion_square(r, c, piece_at.color):
                promo = "Q"
            vr1, vc1 = board_to_visual(fr, fc)
            vr2, vc2 = board_to_visual(r, c)
            move_anim = {
                "piece_key": piece_at.type + piece_at.color,
                "from_vr": vr1, "from_vc": vc1, "to_vr": vr2, "to_vc": vc2,
                "piece_br": fr, "piece_bc": fc, "to_br": r, "to_bc": c,
                "start_ms": pg.time.get_ticks(),
            }
            apply_move({"from": [fr, fc], "to": [r, c], "promotion": promo})
            send_move((fr, fc), (r, c), promotion=promo)
            selected = None
            legal_moves = []
        else:
            selected = None
            legal_moves = []

# ── GAME LOOP ─────────────────────────────────────────────────────────────────
clock = pg.time.Clock()
running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        if event.type == pg.MOUSEBUTTONDOWN:
            pos = event.pos
            input_active = input_rect.collidepoint(pos)
            if btn_create.collidepoint(pos) and not connected:
                create_room()
            elif btn_join.collidepoint(pos) and not connected and len(code_input) == 8:
                join_room()
            elif not any(rect.collidepoint(pos) for rect in (btn_create, btn_join, input_rect)):
                handle_click(*pos)

        if event.type == pg.KEYDOWN and input_active:
            if event.key == pg.K_BACKSPACE:
                code_input = code_input[:-1]
            elif event.key == pg.K_RETURN and len(code_input) == 8 and not connected:
                join_room()
            elif len(code_input) < 8 and event.unicode.isalpha():
                code_input += event.unicode.upper()

    screen.fill((18, 18, 18))
    draw_pieces_and_board()
    draw_arrow()
    draw_ui()
    pg.display.flip()
    clock.tick(60)

try:
    if ws:
        ws.close()
except Exception:
    pass
pg.quit()
