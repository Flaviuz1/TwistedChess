from typing import Optional


class ChessPiece:
    def __init__(self, type: str, color: str, number: Optional[int] = None):
        self.type = type   # "P","R","N","B","Q","K"
        self.color = color  # "w" or "b"
        self.number = number
        self.has_moved = False
        self.can_castle_kingside = (type == "K")
        self.can_castle_queenside = (type == "K")

    def id(self) -> str:
        n = str(self.number) if self.number is not None else "0"
        return f"{self.type}{n}{self.color}"


def _on_board(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


class Board:
    def __init__(self):
        self.grid: list[list[Optional[ChessPiece]]] = [[None] * 8 for _ in range(8)]
        self.rotation = 0
        self.castling: dict[str, dict[str, Optional[tuple[int, int]]]] = {
            "w": {"king": (7, 4), "rook_k": (7, 7), "rook_q": (7, 0)},
            "b": {"king": (0, 4), "rook_k": (0, 7), "rook_q": (0, 0)},
        }
        self._place_pieces()

    def _place_pieces(self) -> None:
        # Queen on its color: white Q on d1 (light), black Q on d8 (dark). Standard: R,N,B,Q,K,B,N,R
        back_b = ["R", "N", "B", "Q", "K", "B", "N", "R"]
        for col, t in enumerate(back_b):
            num = 0 if t in ("R", "N", "B") and col < 4 else (1 if t in ("R", "N", "B") else None)
            self.grid[0][col] = ChessPiece(t, "b", num)
        for col in range(8):
            self.grid[1][col] = ChessPiece("P", "b", col)
        for col in range(8):
            self.grid[6][col] = ChessPiece("P", "w", col)
        back_w = ["R", "N", "B", "Q", "K", "B", "N", "R"]
        for col, t in enumerate(back_w):
            num = 0 if t in ("R", "N", "B") and col < 4 else (1 if t in ("R", "N", "B") else None)
            self.grid[7][col] = ChessPiece(t, "w", num)

    def get(self, r: int, c: int) -> Optional[ChessPiece]:
        if not _on_board(r, c):
            return None
        return self.grid[r][c]

    def _is_square_attacked(self, r: int, c: int, by_color: str) -> bool:
        """Check if (r, c) is attacked by any piece of by_color."""
        # Pawns
        dr = -1 if by_color == "w" else 1
        for dc in (-1, 1):
            nr, nc = r - dr, c + dc
            if _on_board(nr, nc):
                p = self.grid[nr][nc]
                if p and p.type == "P" and p.color == by_color:
                    return True
        # Knights
        for mr, mc in ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)):
            nr, nc = r + mr, c + mc
            if _on_board(nr, nc):
                p = self.grid[nr][nc]
                if p and p.type == "N" and p.color == by_color:
                    return True
        # King (one step)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if _on_board(nr, nc):
                    p = self.grid[nr][nc]
                    if p and p.type == "K" and p.color == by_color:
                        return True
        # Rook/Queen along ranks and files
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r + dr, c + dc
            while _on_board(nr, nc):
                p = self.grid[nr][nc]
                if p:
                    if p.color == by_color and p.type in ("R", "Q"):
                        return True
                    break
                nr, nc = nr + dr, nc + dc
        # Bishop/Queen diagonals
        for dr, dc in ((-1,-1),(-1,1),(1,-1),(1,1)):
            nr, nc = r + dr, c + dc
            while _on_board(nr, nc):
                p = self.grid[nr][nc]
                if p:
                    if p.color == by_color and p.type in ("B", "Q"):
                        return True
                    break
                nr, nc = nr + dr, nc + dc
        return False

    def is_in_check(self, color: str) -> bool:
        pos = self.find_piece("K", color)
        if pos is None:
            return False
        r, c = pos
        opp = "b" if color == "w" else "w"
        return self._is_square_attacked(r, c, opp)

    def _raw_moves(self, r: int, c: int) -> list[tuple[int, int]]:
        """Moves for piece at (r,c) without check filtering. No promotion info here."""
        if not _on_board(r, c):
            return []
        piece = self.grid[r][c]
        if not piece:
            return []
        color = piece.color
        moves: list[tuple[int, int]] = []
        dr_pawn = -1 if color == "w" else 1
        start_row_pawn = 6 if color == "w" else 1

        if piece.type == "P":
            # One forward
            nr, nc = r + dr_pawn, c
            if _on_board(nr, nc) and self.grid[nr][nc] is None:
                moves.append((nr, nc))
            # Two from start
            if r == start_row_pawn:
                nr2 = r + 2 * dr_pawn
                if _on_board(nr2, nc) and self.grid[nr2][nc] is None and self.grid[nr][nc] is None:
                    moves.append((nr2, nc))
            # Captures
            for dc in (-1, 1):
                nr, nc = r + dr_pawn, c + dc
                if _on_board(nr, nc) and self.grid[nr][nc] is not None and self.grid[nr][nc].color != color:
                    moves.append((nr, nc))

        elif piece.type == "N":
            for mr, mc in ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)):
                nr, nc = r + mr, c + mc
                if _on_board(nr, nc):
                    p = self.grid[nr][nc]
                    if p is None or p.color != color:
                        moves.append((nr, nc))

        elif piece.type in ("R", "Q"):
            for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                nr, nc = r + dr, c + dc
                while _on_board(nr, nc):
                    p = self.grid[nr][nc]
                    if p is None:
                        moves.append((nr, nc))
                    else:
                        if p.color != color:
                            moves.append((nr, nc))
                        break
                    nr, nc = nr + dr, nc + dc
        if piece.type in ("B", "Q"):
            for dr, dc in ((-1,-1),(-1,1),(1,-1),(1,1)):
                nr, nc = r + dr, c + dc
                while _on_board(nr, nc):
                    p = self.grid[nr][nc]
                    if p is None:
                        moves.append((nr, nc))
                    else:
                        if p.color != color:
                            moves.append((nr, nc))
                        break
                    nr, nc = nr + dr, nc + dc

        elif piece.type == "K":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if _on_board(nr, nc):
                        p = self.grid[nr][nc]
                        if p is None or p.color != color:
                            moves.append((nr, nc))
            # Castling
            kpos = self.castling[color]["king"]
            if piece.can_castle_kingside and kpos == (r, c):
                rk = self.castling[color]["rook_k"]
                if rk is not None:
                    rr, rc = rk
                    # squares between must be empty and not under attack
                    empty = all(self.grid[r][x] is None for x in range(c + 1, 7))
                    if empty and not self._is_square_attacked(r, c, "b" if color == "w" else "w") and not self._is_square_attacked(r, c + 1, "b" if color == "w" else "w") and not self._is_square_attacked(r, c + 2, "b" if color == "w" else "w"):
                        moves.append((r, c + 2))
            if piece.can_castle_queenside and kpos == (r, c):
                rq = self.castling[color]["rook_q"]
                if rq is not None:
                    empty = all(self.grid[r][x] is None for x in range(1, c))
                    opp = "b" if color == "w" else "w"
                    if empty and not self._is_square_attacked(r, c, opp) and not self._is_square_attacked(r, c - 1, opp) and not self._is_square_attacked(r, c - 2, opp):
                        moves.append((r, c - 2))

        return moves

    def get_legal_moves(self, r: int, c: int) -> list[tuple[int, int]]:
        """Returns list of (tr, tc) that are legal (don't leave own king in check)."""
        piece = self.grid[r][c]
        if not piece or not _on_board(r, c):
            return []
        color = piece.color
        raw = self._raw_moves(r, c)
        legal = []
        for (tr, tc) in raw:
            if not self._move_leaves_king_safe(r, c, tr, tc, piece):
                continue
            legal.append((tr, tc))
        return legal

    def _move_leaves_king_safe(self, fr: int, fc: int, tr: int, tc: int, piece: ChessPiece) -> bool:
        """After moving piece from (fr,fc) to (tr,tc), is own king not in check? Handles castling (moves rook)."""
        captured = self.grid[tr][tc]
        self._apply_raw_move(fr, fc, tr, tc, piece)
        safe = not self.is_in_check(piece.color)
        self._undo_raw_move(fr, fc, tr, tc, piece, captured)
        return safe

    def _apply_raw_move(self, fr: int, fc: int, tr: int, tc: int, piece: ChessPiece) -> None:
        """Apply move without updating has_moved/castling (for try-out). Handles castling rook move."""
        self.grid[fr][fc] = None
        self.grid[tr][tc] = piece
        if piece.type == "K" and abs(tc - fc) == 2:
            if tc > fc:  # kingside: rook from 7 to tc-1
                rook = self.grid[fr][7]
                if rook:
                    self.grid[fr][7] = None
                    self.grid[fr][tc - 1] = rook
            else:  # queenside: rook from 0 to tc+1
                rook = self.grid[fr][0]
                if rook:
                    self.grid[fr][0] = None
                    self.grid[fr][tc + 1] = rook

    def _undo_raw_move(self, fr: int, fc: int, tr: int, tc: int, piece: ChessPiece, captured: Optional[ChessPiece]) -> None:
        """Undo _apply_raw_move."""
        self.grid[fr][fc] = piece
        self.grid[tr][tc] = captured
        if piece.type == "K" and abs(tc - fc) == 2:
            if tc > fc:
                rook = self.grid[fr][tc - 1]
                if rook:
                    self.grid[fr][tc - 1] = None
                    self.grid[fr][7] = rook
            else:
                rook = self.grid[fr][tc + 1]
                if rook:
                    self.grid[fr][tc + 1] = None
                    self.grid[fr][0] = rook

    def move(self, fr: int, fc: int, tr: int, tc: int, promotion: Optional[str] = None) -> None:
        if not (_on_board(fr, fc) and _on_board(tr, tc)):
            return
        piece = self.grid[fr][fc]
        if not piece:
            return
        color = piece.color
        # Castling: move rook
        if piece.type == "K" and abs(tc - fc) == 2:
            if tc > fc:  # kingside
                rook = self.grid[fr][7]
                if rook:
                    self.grid[fr][7] = None
                    self.grid[fr][tc - 1] = rook
                    rook.has_moved = True
            else:  # queenside
                rook = self.grid[fr][0]
                if rook:
                    self.grid[fr][0] = None
                    self.grid[fr][tc + 1] = rook
                    rook.has_moved = True

        piece.has_moved = True
        if piece.type == "K":
            self.castling[color]["king"] = (tr, tc)
            piece.can_castle_kingside = False
            piece.can_castle_queenside = False
        if piece.type == "R":
            if (fr, fc) == self.castling[color]["rook_k"]:
                self.castling[color]["rook_k"] = None
            if (fr, fc) == self.castling[color]["rook_q"]:
                self.castling[color]["rook_q"] = None

        captured = self.grid[tr][tc]
        if captured and captured.type == "R":
            cap_color = captured.color
            if (tr, tc) == self.castling[cap_color]["rook_k"]:
                self.castling[cap_color]["rook_k"] = None
            if (tr, tc) == self.castling[cap_color]["rook_q"]:
                self.castling[cap_color]["rook_q"] = None

        self.grid[tr][tc] = piece
        self.grid[fr][fc] = None

        # Promotion: pawn reaches opposite original back rank
        if piece.type == "P" and self._is_promotion_square(tr, tc, color):
            promo = (promotion or "Q").upper()
            if promo not in ("Q", "R", "N", "B"):
                promo = "Q"
            self.grid[tr][tc] = ChessPiece(promo, color)

    def _is_promotion_square(self, tr: int, tc: int, color: str) -> bool:
        """Check if (tr,tc) is the promotion rank for color, given current board rotation."""
        r = self.rotation
        if color == "w":
            return (r == 0 and tr == 0) or (r == 1 and tc == 7) or (r == 2 and tr == 7) or (r == 3 and tc == 0)
        else:
            return (r == 0 and tr == 7) or (r == 1 and tc == 0) or (r == 2 and tr == 0) or (r == 3 and tc == 7)

    def rotate_board(self) -> None:
        new_grid: list[list[Optional[ChessPiece]]] = [[None] * 8 for _ in range(8)]
        for r in range(8):
            for c in range(8):
                new_grid[c][7 - r] = self.grid[r][c]
        self.grid = new_grid
        self.rotation = (self.rotation + 1) % 4
        for color in ("w", "b"):
            kr, kc = self.castling[color]["king"]  # type: ignore
            self.castling[color]["king"] = (kc, 7 - kr)
            if self.castling[color]["rook_k"] is not None:
                rr, rc = self.castling[color]["rook_k"]  # type: ignore
                self.castling[color]["rook_k"] = (rc, 7 - rr)
            if self.castling[color]["rook_q"] is not None:
                rr, rc = self.castling[color]["rook_q"]  # type: ignore
                self.castling[color]["rook_q"] = (rc, 7 - rr)

    def is_checkmate(self, color: str) -> bool:
        if not self.is_in_check(color):
            return False
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.color == color and self.get_legal_moves(r, c):
                    return False
        return True

    def find_piece(self, piece_type: str, color: str) -> Optional[tuple[int, int]]:
        """Find first piece of given type and color. Returns (r, c) or None."""
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.type == piece_type and p.color == color:
                    return (r, c)
        return None
