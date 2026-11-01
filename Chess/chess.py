# Chess

# Import the required libraries
import pygame
import math
import array
from sys import exit

# Initialize Pygame
pygame.init()

# Create a screen with a title
screen = pygame.display.set_mode((1540, 800))
pygame.display.set_caption("Chess")

# Create a Clock object
clock = pygame.time.Clock()

# Size of a single block
block_size = 75

# Top left corner of the board
board_left = (screen.get_width() - 8 * block_size) // 2
board_top = (screen.get_height() - 8 * block_size) // 2

# Fonts are created once instead of every frame
label_font = pygame.font.SysFont("Bold", 40)
end_font = pygame.font.SysFont(None, 40)

# Folder of the piece images and a cache so each image loads only once
IMAGE_PATH = "Chess Engine/chess pieces"
image_cache = {}

# Stores the generated sounds
sounds = {}

# Loads, scales and caches a piece image
def load_image(color, name):
    key = (color, name)
    if key not in image_cache:
        image = pygame.image.load(f"{IMAGE_PATH}/{color}_{name}.png").convert_alpha()
        if name == "pawn":
            size = (int(block_size * 0.7), int(block_size * 0.8))
        else:
            size = (int(block_size * 0.9), int(block_size * 0.9))
        image_cache[key] = pygame.transform.scale(image, size)
    return image_cache[key]


# Collects the moves of a sliding piece in the given directions
def get_sliding_moves(piece, board, directions):
    legal_moves = []
    col, row = piece.position
    for dc, dr in directions:
        c, r = col + dc, row + dr
        while 0 <= c < 8 and 0 <= r < 8:
            if board[r][c] is None:
                legal_moves.append((c, r))
            else:
                if board[r][c].color != piece.color:
                    legal_moves.append((c, r))
                break
            c += dc
            r += dr
    return legal_moves

# Class for Pieces
class Piece:
    def __init__(self, color, position):
        self.color = color
        self.position = position
        self.image = load_image(color, type(self).__name__.lower())

# Class for Pawn
class Pawn(Piece):

    # Generates the legal moves for the pawn
    def get_legal_moves(self, board, en_passant_target):
        legal_moves = []
        col, row = self.position
        direction = -1 if self.color == "white" else 1
        enemy_color = "black" if self.color == "white" else "white"

        # Forward moves
        if 0 <= row + direction <= 7 and board[row + direction][col] is None:
            legal_moves.append((col, row + direction))
            if row == (6 if self.color == "white" else 1) and board[row + 2 * direction][col] is None:
                legal_moves.append((col, row + 2 * direction))

        # Diagonal captures and en passant
        for dc in (-1, 1):
            new_col = col + dc
            new_row = row + direction
            if 0 <= new_col <= 7 and 0 <= new_row <= 7:
                target = board[new_row][new_col]
                if target is not None and target.color == enemy_color:
                    legal_moves.append((new_col, new_row))
                elif (new_col, new_row) == en_passant_target:
                    legal_moves.append((new_col, new_row))
        return legal_moves

# Class for Knight
class Knight(Piece):

    # Generates the legal moves for the knight
    def get_legal_moves(self, board):
        legal_moves = []
        col, row = self.position
        for dc, dr in [(1, 2), (-1, 2), (1, -2), (-1, -2), (2, 1), (-2, 1), (2, -1), (-2, -1)]:
            c, r = col + dc, row + dr
            if 0 <= c < 8 and 0 <= r < 8 and (board[r][c] is None or board[r][c].color != self.color):
                legal_moves.append((c, r))
        return legal_moves

# Class for Bishop
class Bishop(Piece):

    # Generates the legal moves for the bishop
    def get_legal_moves(self, board):
        return get_sliding_moves(self, board, [(-1, -1), (1, -1), (-1, 1), (1, 1)])

# Class for Rook
class Rook(Piece):
    def __init__(self, color, position, has_moved=False):
        super().__init__(color, position)
        self.has_moved = has_moved

    # Generates the legal moves for the rook
    def get_legal_moves(self, board):
        return get_sliding_moves(self, board, [(0, -1), (0, 1), (-1, 0), (1, 0)])

# Class for Queen
class Queen(Piece):

    # Generates the legal moves for the queen
    def get_legal_moves(self, board):
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]
        return get_sliding_moves(self, board, directions)

# Class for King
class King(Piece):
    def __init__(self, color, position, has_moved=False):
        super().__init__(color, position)
        self.has_moved = has_moved

    # Generates the legal moves for the king
    def get_legal_moves(self, board):
        legal_moves = []
        col, row = self.position
        for dc, dr in [(1, 0), (1, -1), (1, 1), (-1, 0), (-1, -1), (-1, 1), (0, -1), (0, 1)]:
            c, r = col + dc, row + dr
            if 0 <= c < 8 and 0 <= r < 8 and (board[r][c] is None or board[r][c].color != self.color):
                legal_moves.append((c, r))

        # For castling
        if not self.has_moved:
            right_rook = board[row][7]
            if isinstance(right_rook, Rook) and right_rook.color == self.color and not right_rook.has_moved:
                if board[row][5] is None and board[row][6] is None:
                    legal_moves.append((6, row))
            left_rook = board[row][0]
            if isinstance(left_rook, Rook) and left_rook.color == self.color and not left_rook.has_moved:
                if board[row][1] is None and board[row][2] is None and board[row][3] is None:
                    legal_moves.append((2, row))
        return legal_moves

# Class for creating the chess board
class ChessBoard:

    # Draws the board
    @staticmethod
    def draw_chess_board(screen, block_size):

        # Draws the blocks of the board
        for row in range(8):
            for col in range(8):
                color = (181, 136, 99) if (row + col) % 2 == 1 else (240, 217, 181)
                pygame.draw.rect(screen, color, (board_left + block_size * col, board_top + block_size * row, block_size, block_size))

        # Draws the border
        pygame.draw.rect(screen, (0, 0, 0), (board_left, board_top, block_size * 8, block_size * 8), 2)

        # Draws the numbers and letters of the rows and columns
        letters = ["a", "b", "c", "d", "e", "f", "g", "h"]
        for i in range(8):
            number_text = label_font.render(str(i + 1), True, (0, 0, 0))
            number_rect = number_text.get_rect(center=(board_left - (block_size // 10 * 3), board_top + block_size * (7.5 - i)))
            screen.blit(number_text, number_rect)
            letter_text = label_font.render(letters[i], True, (0, 0, 0))
            letter_rect = letter_text.get_rect(center=(board_left + block_size * (0.5 + i), board_top + block_size * 8.3))
            screen.blit(letter_text, letter_rect)

# Class for the Game
class ChessGame:

    # Contains the information of the board
    def __init__(self):

        # Game result information
        self.game_over = False
        self.reason = ""

        # Whose turn it is and which color is in check
        self.turn = "white"
        self.checked_color = None

        # Square skipped by a pawn that just moved two squares
        self.en_passant_target = None

        # Selection and dragging information
        self.selected_piece = None
        self.selected_position = None
        self.legal_moves = []
        self.dragging = False
        self.mouse_position = None

        # White pieces
        self.white_pawn_1 = Pawn("white", (0, 6))
        self.white_pawn_2 = Pawn("white", (1, 6))
        self.white_pawn_3 = Pawn("white", (2, 6))
        self.white_pawn_4 = Pawn("white", (3, 6))
        self.white_pawn_5 = Pawn("white", (4, 6))
        self.white_pawn_6 = Pawn("white", (5, 6))
        self.white_pawn_7 = Pawn("white", (6, 6))
        self.white_pawn_8 = Pawn("white", (7, 6))

        self.white_rook_1 = Rook("white", (0, 7))
        self.white_knight_1 = Knight("white", (1, 7))
        self.white_bishop_1 = Bishop("white", (2, 7))
        self.white_queen = Queen("white", (3, 7))
        self.white_king = King("white", (4, 7))
        self.white_bishop_2 = Bishop("white", (5, 7))
        self.white_knight_2 = Knight("white", (6, 7))
        self.white_rook_2 = Rook("white", (7, 7))

        # Black pieces
        self.black_pawn_1 = Pawn("black", (0, 1))
        self.black_pawn_2 = Pawn("black", (1, 1))
        self.black_pawn_3 = Pawn("black", (2, 1))
        self.black_pawn_4 = Pawn("black", (3, 1))
        self.black_pawn_5 = Pawn("black", (4, 1))
        self.black_pawn_6 = Pawn("black", (5, 1))
        self.black_pawn_7 = Pawn("black", (6, 1))
        self.black_pawn_8 = Pawn("black", (7, 1))

        self.black_rook_1 = Rook("black", (0, 0))
        self.black_knight_1 = Knight("black", (1, 0))
        self.black_bishop_1 = Bishop("black", (2, 0))
        self.black_queen = Queen("black", (3, 0))
        self.black_king = King("black", (4, 0))
        self.black_bishop_2 = Bishop("black", (5, 0))
        self.black_knight_2 = Knight("black", (6, 0))
        self.black_rook_2 = Rook("black", (7, 0))

        # Board as a grid of pieces, None means an empty square
        self.board = [[self.black_rook_1, self.black_knight_1, self.black_bishop_1, self.black_queen, self.black_king, self.black_bishop_2, self.black_knight_2, self.black_rook_2],
                      [self.black_pawn_1, self.black_pawn_2, self.black_pawn_3, self.black_pawn_4, self.black_pawn_5, self.black_pawn_6, self.black_pawn_7, self.black_pawn_8],
                      [None, None, None, None, None, None, None, None],
                      [None, None, None, None, None, None, None, None],
                      [None, None, None, None, None, None, None, None],
                      [None, None, None, None, None, None, None, None],
                      [self.white_pawn_1, self.white_pawn_2, self.white_pawn_3, self.white_pawn_4, self.white_pawn_5, self.white_pawn_6, self.white_pawn_7, self.white_pawn_8],
                      [self.white_rook_1, self.white_knight_1, self.white_bishop_1, self.white_queen, self.white_king, self.white_bishop_2, self.white_knight_2, self.white_rook_2]]

    # Selects a piece and calculates its legal moves once
    def select_piece(self, piece, position, mouse_position):
        self.selected_piece = piece
        self.selected_position = position
        self.mouse_position = mouse_position
        self.legal_moves = self.get_legal_moves(piece)

    # Resets the selection variables
    def clear_selection(self):
        self.selected_piece = None
        self.selected_position = None
        self.legal_moves = []
        self.dragging = False
        self.mouse_position = None

    # Draws the pieces except the one being dragged
    def place_piece(self, screen, block_size):
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and not (piece is self.selected_piece and self.dragging):
                    x = board_left + block_size * (col + 0.5)
                    y = board_top + block_size * (row + 0.5)
                    screen.blit(piece.image, piece.image.get_rect(center=(x, y)))

    # Gives the moves of any piece without considering king's safety
    def get_pseudo_legal_moves(self, piece):
        if isinstance(piece, Pawn):
            return piece.get_legal_moves(self.board, self.en_passant_target)
        return piece.get_legal_moves(self.board)

    # Checks whether a square is attacked by a color
    def is_square_attacked(self, square, by_color):
        col, row = square
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece is None or piece.color != by_color:
                    continue
                if isinstance(piece, Pawn):
                    direction = -1 if piece.color == "white" else 1
                    if square in ((c - 1, r + direction), (c + 1, r + direction)):
                        return True
                elif isinstance(piece, King):
                    if max(abs(c - col), abs(r - row)) == 1:
                        return True
                else:
                    if square in piece.get_legal_moves(self.board):
                        return True
        return False

    # Checks whether the king of a color is in check
    def is_in_check(self, color):
        king = self.white_king if color == "white" else self.black_king
        enemy = "black" if color == "white" else "white"
        return self.is_square_attacked(king.position, enemy)

    # Generates legal moves that keep the king safe
    def get_legal_moves(self, piece):
        safe_moves = []
        old_col, old_row = piece.position
        enemy = "black" if piece.color == "white" else "white"
        for col, row in self.get_pseudo_legal_moves(piece):

            # Checks for castling legality
            if isinstance(piece, King) and abs(col - old_col) == 2:
                if self.is_in_check(piece.color):
                    continue
                middle = (old_col + (col - old_col) // 2, old_row)
                if self.is_square_attacked(middle, enemy):
                    continue

            # Simulates the move
            captured = self.board[row][col]
            ep_captured = None

            # En passant captures the pawn beside the moving pawn
            if isinstance(piece, Pawn) and col != old_col and captured is None:
                ep_captured = self.board[old_row][col]
                self.board[old_row][col] = None

            self.board[row][col] = piece
            self.board[old_row][old_col] = None
            piece.position = (col, row)

            # Keeps the move only if the own king is safe
            if not self.is_in_check(piece.color):
                safe_moves.append((col, row))

            # Undoes the move
            piece.position = (old_col, old_row)
            self.board[old_row][old_col] = piece
            self.board[row][col] = captured
            if ep_captured is not None:
                self.board[old_row][col] = ep_captured
        return safe_moves

    # Checks whether a color has any legal move
    def has_any_legal_move(self, color):
        for row in self.board:
            for piece in row:
                if piece is not None and piece.color == color:
                    if self.get_legal_moves(piece):
                        return True
        return False

    # Checks for a draw because no one can checkmate
    def is_insufficient_material(self):
        pieces = [piece for row in self.board for piece in row if piece is not None and not isinstance(piece, King)]
        if len(pieces) == 0:
            return True
        if len(pieces) == 1 and isinstance(pieces[0], (Bishop, Knight)):
            return True
        if all(isinstance(piece, Bishop) for piece in pieces):
            return len({(piece.position[0] + piece.position[1]) % 2 for piece in pieces}) == 1
        return False

# Creates the objects that are used in the main game loop
cb = ChessBoard()
cg = ChessGame()

# Generates the sounds for different events
def init_sounds():
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
    except Exception:
        return
    sample_rate = 44100

    # Creates a short fading tone that slides from one pitch to another
    def make_tone(freq_start, freq_end, duration_sec, volume=0.4, decay=12.0):
        num_samples = int(sample_rate * duration_sec)
        buf = array.array("h", [0] * num_samples)
        phase = 0.0
        for i in range(num_samples):
            t = i / sample_rate
            progress = i / num_samples
            freq = freq_start + (freq_end - freq_start) * progress
            phase += 2.0 * math.pi * freq / sample_rate
            env = math.exp(-decay * t)
            sample = int(32767 * volume * env * math.sin(phase))
            buf[i] = max(-32768, min(32767, sample))
        return pygame.mixer.Sound(buffer=buf)

    # Stores the sounds in a dictionary for easy access
    sounds["move"] = make_tone(190, 75, 0.065, volume=0.45, decay=28.0)
    sounds["capture"] = make_tone(280, 65, 0.085, volume=0.55, decay=22.0)
    sounds["castle"] = make_tone(160, 110, 0.11, volume=0.45, decay=18.0)
    sounds["promote"] = make_tone(320, 640, 0.16, volume=0.4, decay=10.0)
    sounds["check"] = make_tone(580, 420, 0.22, volume=0.45, decay=9.0)
    sounds["game_over"] = make_tone(440, 220, 0.45, volume=0.5, decay=5.0)
init_sounds()

# Plays a sound if the mixer is available
def play_sound(name):
    if name in sounds:
        sounds[name].play()

# Pawn that is waiting for the player to choose its promotion piece
promoting = None

# Cache for the promotion menu surfaces
promotion_surfaces = {}

# Gives the top left position of the promotion menu
def get_promotion_position(color, col):
    x = board_left + block_size * col
    y = board_top if color == "white" else board_top + block_size * 7
    return x, y

# Creates the menu from which the player picks the promotion piece
def promotion(color, x, y):
    if color not in promotion_surfaces:
        surface = pygame.Surface((block_size * 4, block_size))
        surface.fill((255, 255, 0))
        for i, name in enumerate(("queen", "rook", "bishop", "knight")):
            image = load_image(color, name)
            surface.blit(image, (block_size * i + (block_size - image.get_width()) // 2, (block_size - image.get_height()) // 2))
        promotion_surfaces[color] = surface
    surface = promotion_surfaces[color]
    return surface, surface.get_rect(topleft=(x, y))

# Switches the turn, checks the game state and plays the right sound
def finish_turn(sound):
    cg.turn = "white" if cg.turn == "black" else "black"
    in_check = cg.is_in_check(cg.turn)
    cg.checked_color = cg.turn if in_check else None

    # Checks for checkmate, stalemate and insufficient material
    if not cg.has_any_legal_move(cg.turn):
        cg.game_over = True
        if in_check:
            cg.reason = "checkmate"
    elif cg.is_insufficient_material():
        cg.game_over = True

    # One sound per move, the most important one wins
    if cg.game_over:
        play_sound("game_over")
    elif in_check:
        play_sound("check")
    else:
        play_sound(sound)

# Writes the result of the game on the screen
def end_game_message(turn, reason):
    winner = "White" if turn == "black" else "Black"
    text = f"{winner} Won, Game Over!" if reason == "checkmate" else "It's a draw, Game Over!"
    banner = pygame.Surface((screen.get_width(), 50), pygame.SRCALPHA)
    banner.fill((0, 0, 0, 150))
    message = end_font.render(text, True, (255, 255, 255))
    banner.blit(message, message.get_rect(center=banner.get_rect().center))
    screen.blit(banner, banner.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2)))

# Moves the selected piece to the square under the mouse
def move_piece(pos):
    global promoting

    # Calculates the destination block
    col = (pos[0] - board_left) // block_size
    row = (pos[1] - board_top) // block_size
    piece = cg.selected_piece
    old_col, old_row = cg.selected_position

    if (col, row) in cg.legal_moves:
        sound = "move"
        if cg.board[row][col] is not None:
            sound = "capture"

        # Captures the pawn that is taken by en passant
        if isinstance(piece, Pawn) and col != old_col and (col, row) == cg.en_passant_target:
            cg.board[old_row][col] = None
            sound = "capture"

        # Moves the rook when castling
        if isinstance(piece, King) and abs(col - old_col) == 2:
            step = 1 if col > old_col else -1
            rook_col = 7 if step == 1 else 0
            rook = cg.board[old_row][rook_col]
            cg.board[old_row][old_col + step] = rook
            cg.board[old_row][rook_col] = None
            rook.position = (old_col + step, old_row)
            rook.has_moved = True
            sound = "castle"

        # Makes the basic move
        cg.board[row][col] = piece
        cg.board[old_row][old_col] = None
        piece.position = (col, row)
        if isinstance(piece, (King, Rook)):
            piece.has_moved = True

        # Remembers the square that can be taken by en passant on the next move
        if isinstance(piece, Pawn) and abs(row - old_row) == 2:
            cg.en_passant_target = (col, (row + old_row) // 2)
        else:
            cg.en_passant_target = None

        cg.clear_selection()

        # The turn ends after the promotion piece is chosen
        if isinstance(piece, Pawn) and row in (0, 7):
            promoting = piece
        else:
            finish_turn(sound)
        return

    # Illegal destination
    cg.clear_selection()

# Handles the mouse button press
def handle_mouse_button_down(event):
    global promoting

    # Only the left button is used
    if event.button != 1:
        return

    # While promoting only the promotion menu works
    if promoting is not None:
        color = promoting.color
        col, row = promoting.position
        x, y = get_promotion_position(color, col)
        if pygame.Rect(x, y, block_size * 4, block_size).collidepoint(event.pos):
            piece_class = [Queen, Rook, Bishop, Knight][(event.pos[0] - x) // block_size]
            new_piece = piece_class(color, (col, row))
            if isinstance(new_piece, Rook):
                new_piece.has_moved = True
            cg.board[row][col] = new_piece
            promoting = None
            finish_turn("promote")
        return

    if cg.game_over:
        return

    # Calculates the clicked block
    col = (event.pos[0] - board_left) // block_size
    row = (event.pos[1] - board_top) // block_size

    # Clicking outside the board deselects
    if not (0 <= col < 8 and 0 <= row < 8):
        cg.clear_selection()
        return

    clicked_piece = cg.board[row][col]
    if clicked_piece is not None and clicked_piece.color == cg.turn:
        cg.select_piece(clicked_piece, (col, row), event.pos)
    elif cg.selected_piece is not None and (col, row) in cg.legal_moves:
        move_piece(event.pos)
    else:
        cg.clear_selection()

# Main game loop
while True:

    # Process events such as clicks and window closing
    for event in pygame.event.get():

        # Close Pygame when the window is closed
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # Handles piece selection and click movement
        elif event.type == pygame.MOUSEBUTTONDOWN:
            handle_mouse_button_down(event)

        # Starts or updates the dragging
        elif event.type == pygame.MOUSEMOTION:
            if cg.selected_piece is not None and pygame.mouse.get_pressed()[0]:
                cg.dragging = True
                cg.mouse_position = event.pos

        # Drops the dragged piece
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and cg.dragging:
                move_piece(event.pos)

    # Colors the screen and draws the board
    screen.fill((255, 255, 255))
    cb.draw_chess_board(screen, block_size)

    # Draws all the pieces
    cg.place_piece(screen, block_size)

    # Draws a red square around the king in check
    if cg.checked_color is not None:
        king = cg.white_king if cg.checked_color == "white" else cg.black_king
        king_x = board_left + king.position[0] * block_size
        king_y = board_top + king.position[1] * block_size
        pygame.draw.rect(screen, (255, 0, 0), (king_x, king_y, block_size, block_size), 5)

    # Draws a red dot on the legal squares
    for dot_col, dot_row in cg.legal_moves:
        dot_x = board_left + (dot_col + 0.5) * block_size
        dot_y = board_top + (dot_row + 0.5) * block_size
        pygame.draw.circle(screen, (255, 0, 0), (dot_x, dot_y), 10)

    # Draws the dragged piece above everything else
    if cg.dragging and cg.selected_piece is not None:
        piece_image = cg.selected_piece.image
        screen.blit(piece_image, piece_image.get_rect(center=cg.mouse_position))

    # Draws the result of the game
    if cg.game_over:
        end_game_message(cg.turn, cg.reason)

    # Draws the promotion menu
    if promoting is not None:
        menu_x, menu_y = get_promotion_position(promoting.color, promoting.position[0])
        surface, rect = promotion(promoting.color, menu_x, menu_y)
        screen.blit(surface, rect)

    # Updates the screen at 60 FPS
    pygame.display.update()
    clock.tick(60)
