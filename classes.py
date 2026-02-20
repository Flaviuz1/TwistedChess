class Board:
    def __init__(self):
        self.grid = [
            ["R0b", "N0b", "B0b", "Q0b", "K0b", "B1b", "N1b", "R1b"],  # black back row
            ["P0b", "P1b", "P2b", "P3b", "P4b", "P5b", "P6b", "P7b"],  # black pawns
            ["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "],
            ["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "],
            ["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "],
            ["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "],
            ["P0w", "P1w", "P2w", "P3w", "P4w", "P5w", "P6w", "P7w"],  # white pawns
            ["R0w", "N0w", "B0w", "Q0w", "K0w", "B1w", "N1w", "R1w"],  # white back row
        ]

    def rotate_board(self):
        self.grid = [list(row) for row in zip(*self.grid[::-1])]

class ChessPiece:
    def __init__(self, type, color, number=None):
        self.type = type
        self.color = color
        self.number = number
        self.has_moved = False
        self.pos = self.find_initial_pos()

    def find_initial_pos(self):
        back_row = 7 if self.color == 0 else 0
        match self.type:
            case "P": return (self.number, 6 if self.color == 0 else 1)
            case "R": return (0 if self.number == 0 else 7, back_row)
            case "N": return (1 if self.number == 0 else 6, back_row)
            case "B": return (2 if self.number == 0 else 5, back_row)
            case "Q": return (3, back_row)
            case "K": return (4, back_row)