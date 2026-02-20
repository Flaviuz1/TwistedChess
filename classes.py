import numpy as np

'''
----Piece Notations----
Pawn - 1
Knight - 2
Bishop - 3
Rook - 4
Queen - 5
King - 6

White - 0
Black - 1

example : black rook = 41; white queen = 60
'''

def board(self):
    self.grid = np.matrix([0,0,0,0,0,0,0,0], # <- black
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0]) # <- white

def chess_piece(self, type, color, moved_flag):
    self.type = type[0]
    if self.type != "K" or self.type != "Q":
        self.number = int(type[1])
    self.color = color
    self.has_moved = moved_flag
    
    def find_initial_pos(type, color):
        match type:
            case "P": return (self.number,                                  (6 if self.color == 0 else 1))
            case "K": return (self.number + (1 if self.number == 0 else 6), (0 if self.color == 1 else 7))
            case "B": return (self.number + (2 if self.number == 0 else 5), (0 if self.color == 1 else 7))
            case "R": return (self.number + (0 if self.number == 0 else 7), (0 if self.color == 1 else 7))
            case "Q": return (3,                                            (0 if self.color == 1 else 7))
            case "K": return (4,                                            (0 if self.color == 1 else 7))
    
    self.pos = find_initial_pos