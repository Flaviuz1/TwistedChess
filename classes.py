import numpy as np
from typing import Optional

class ChessPiece:
    def __init__(self, type, color, number=None):
        self.type   = type    # "P","R","N","B","Q","K"
        self.color  = color   # "w" or "b"
        self.number = number  # 0,1 for pieces with multiples
        self.has_moved = False
        self.can_castle_kingside  = (type == "K")
        self.can_castle_queenside = (type == "K")

    def id(self):
        n = str(self.number) if self.number is not None else "0"
        return f"{self.type}{n}{self.color}"  # e.g. "P3w", "K0b"


class Board:
    def __init__(self):
        self.grid: list[list[Optional[ChessPiece]]] = [[None]*8 for _ in range(8)]
        self.rotation = 0
        self.castling: dict[str, dict[str, Optional[tuple[int,int]]]] = {
            "w": {"king": (7,4), "rook_k": (7,7), "rook_q": (7,0)},
            "b": {"king": (0,4), "rook_k": (0,7), "rook_q": (0,0)},
        }
        self._place_pieces()

    def _place_pieces(self):
        # Black back row
        back_b = ["R","N","B","Q","K","B","N","R"]
        for col, t in enumerate(back_b):
            num = None
            if t in ("R","N","B"):
                num = 0 if col < 4 else 1
            self.grid[0][col] = ChessPiece(t, "b", num)
        # Black pawns
        for col in range(8):
            self.grid[1][col] = ChessPiece("P", "b", col)
        # White pawns
        for col in range(8):
            self.grid[6][col] = ChessPiece("P", "w", col)
        # White back row
        back_w = ["R","N","B","Q","K","B","N","R"]
        for col, t in enumerate(back_w):
            num = None
            if t in ("R","N","B"):
                num = 0 if col < 4 else 1
            self.grid[7][col] = ChessPiece(t, "w", num)

    def get(self, r, c):
        return self.grid[r][c]

    def move(self, fr, fc, tr, tc):
        piece = self.grid[fr][fc]
        if piece:
            piece.has_moved = True
            # Update castling positions if king or rook moved
            color = piece.color
            if piece.type == "K":
                self.castling[color]["king"] = (tr, tc)
                piece.can_castle_kingside  = False
                piece.can_castle_queenside = False
            if piece.type == "R":
                if (fr, fc) == self.castling[color]["rook_k"]:
                    self.castling[color]["rook_k"] = None  # rook moved, no castling
                if (fr, fc) == self.castling[color]["rook_q"]:
                    self.castling[color]["rook_q"] = None
        self.grid[tr][tc] = piece
        self.grid[fr][fc] = None

    def rotate_board(self):
        new_grid: list[list[Optional[ChessPiece]]] = [[None]*8 for _ in range(8)]
        for r in range(8):
            for c in range(8):
                new_grid[c][7-r] = self.grid[r][c]
        self.grid = new_grid
        self.rotation = (self.rotation + 1) % 4

        for color in ("w", "b"):
            kr, kc = self.castling[color]["king"]  # type: ignore
            self.castling[color]["king"] = (kc, 7-kr)
            if self.castling[color]["rook_k"] is not None:
                rr, rc = self.castling[color]["rook_k"]  # type: ignore
                self.castling[color]["rook_k"] = (rc, 7-rr)
            if self.castling[color]["rook_q"] is not None:
                rr, rc = self.castling[color]["rook_q"]  # type: ignore
                self.castling[color]["rook_q"] = (rc, 7-rr)

    def find_piece(self, type, color):
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.type == type and p.color == color:
                    return (r, c)
        return None