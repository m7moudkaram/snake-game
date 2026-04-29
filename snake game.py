"""
Snake Game — main.py
=====================
A complete Pygame Snake game featuring:
  • Real-time Score  (+10 per food eaten)
  • Live Timer       (elapsed seconds since game start)
  • Professional Game Over screen with final stats + restart/quit

Controls during gameplay : Arrow Keys
Controls on Game Over    : R → Restart  |  Q → Quit

Run: python main.py
"""

import pygame
import random
import sys

# ---------------------------------------------------------------------------
# Constants — tweak these to change the feel of the game
# ---------------------------------------------------------------------------
WINDOW_WIDTH  = 800
WINDOW_HEIGHT = 640

CELL_SIZE = 20                          # Grid cell size in pixels
GRID_COLS = WINDOW_WIDTH  // CELL_SIZE  # 40 columns
GRID_ROWS = WINDOW_HEIGHT // CELL_SIZE  # 32 rows

HUD_HEIGHT = 40                         # Height of the top status bar (px)
# The playable area starts below the HUD
PLAY_TOP = HUD_HEIGHT

FPS         = 12    # Base snake speed (frames per second)
SCORE_STEP  = 10    # Points awarded per food item

# ---------------------------------------------------------------------------
# Colour Palette
# ---------------------------------------------------------------------------
C_BG            = (10,  12,  20)    # Near-black background
C_GRID          = (22,  26,  42)    # Subtle grid lines
C_HUD_BG        = (6,   8,  15)    # Darker top bar
C_HUD_BORDER    = (35,  40,  65)    # HUD bottom separator

C_SNAKE_HEAD    = (60,  230, 120)   # Bright green head
C_SNAKE_BODY    = (34,  160,  85)   # Darker green body
C_SNAKE_OUTLINE = (18,   90,  48)   # Thin outline for depth

C_FOOD          = (235,  75,  75)   # Vivid red food
C_FOOD_SHINE    = (255, 160, 160)   # Small highlight dot

C_SCORE_LABEL   = (160, 165, 185)   # Muted label text
C_SCORE_VALUE   = (80,  220, 140)   # Bright green value
C_TIMER_LABEL   = (160, 165, 185)
C_TIMER_VALUE   = (100, 185, 255)   # Blue timer value

C_OVER_OVERLAY  = (0, 0, 0, 185)    # Semi-transparent black overlay
C_OVER_TITLE    = (235,  75,  75)   # Red "GAME OVER"
C_OVER_TEXT     = (200, 205, 220)   # White-ish body text
C_OVER_SCORE    = (80,  220, 140)   # Green final-score line
C_OVER_TIME     = (100, 185, 255)   # Blue time-survived line
C_OVER_RESTART  = (80,  220, 140)   # Restart hint
C_OVER_QUIT     = (235,  75,  75)   # Quit hint
C_DIVIDER       = (50,   55,  85)   # Horizontal divider on overlay

# Direction vectors (Δcol, Δrow)
DIR_UP    = ( 0, -1)
DIR_DOWN  = ( 0,  1)
DIR_LEFT  = (-1,  0)
DIR_RIGHT = ( 1,  0)


# ===========================================================================
# Utility — grid cell → pixel Rect
# ===========================================================================
def cell_rect(col: int, row: int) -> pygame.Rect:
    """Return the pixel Rect for a grid cell, offset below the HUD."""
    return pygame.Rect(
        col * CELL_SIZE,
        row * CELL_SIZE + PLAY_TOP,
        CELL_SIZE,
        CELL_SIZE,
    )


# ===========================================================================
# Food — position + rendering
# ===========================================================================
class Food:
    """Manages the food pellet: random placement and drawing."""

    def __init__(self) -> None:
        self.col = 0
        self.row = 0

    def spawn(self, occupied: set[tuple[int, int]]) -> None:
        """
        Place food on a random empty grid cell.
        Re-rolls until the chosen cell is not occupied by the snake.
        """
        play_rows = (WINDOW_HEIGHT - PLAY_TOP) // CELL_SIZE
        while True:
            col = random.randint(0, GRID_COLS - 1)
            row = random.randint(0, play_rows - 1)
            if (col, row) not in occupied:
                self.col, self.row = col, row
                break

    def draw(self, surface: pygame.Surface) -> None:
        rect = cell_rect(self.col, self.row)
        cx, cy = rect.centerx, rect.centery
        r = CELL_SIZE // 2 - 2
        pygame.draw.circle(surface, C_FOOD,       (cx, cy), r)
        pygame.draw.circle(surface, C_FOOD_SHINE, (cx - 3, cy - 3), r // 3)

    @property
    def position(self) -> tuple[int, int]:
        return (self.col, self.row)


# ===========================================================================
# Snake — body, movement, collision, rendering
# ===========================================================================
class Snake:
    """
    Controls the snake's body (a list of (col, row) tuples).
    body[0] is always the head.
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Place the snake in the centre of the grid, pointing right."""
        mid_col = GRID_COLS // 2
        mid_row = (WINDOW_HEIGHT - PLAY_TOP) // CELL_SIZE // 2
        self.body: list[tuple[int, int]] = [
            (mid_col,     mid_row),
            (mid_col - 1, mid_row),
            (mid_col - 2, mid_row),
        ]
        self.direction   = DIR_RIGHT
        self._queued_dir = DIR_RIGHT
        self.grew        = False
        self.alive       = True

    # ------------------------------------------------------------------
    def queue_direction(self, new_dir: tuple[int, int]) -> None:
        """
        Buffer a direction change.
        Prevents instant 180° reversal (moving into your own neck).
        """
        opposite = (-new_dir[0], -new_dir[1])
        if new_dir != opposite:
            self._queued_dir = new_dir

    # ------------------------------------------------------------------
    def move(self) -> None:
        """
        Advance the snake one cell forward.
        Applies the queued direction, calculates the new head,
        checks wall and self-collision, then shifts the body.
        """
        self.direction = self._queued_dir

        head_col, head_row = self.body[0]
        dc, dr = self.direction
        new_head = (head_col + dc, head_row + dr)

        play_rows = (WINDOW_HEIGHT - PLAY_TOP) // CELL_SIZE

        # Wall collision
        if not (0 <= new_head[0] < GRID_COLS and 0 <= new_head[1] < play_rows):
            self.alive = False
            return

        # Self collision
        if new_head in self.body:
            self.alive = False
            return

        self.body.insert(0, new_head)
        if not self.grew:
            self.body.pop()
        else:
            self.grew = False

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        for i, (col, row) in enumerate(self.body):
            rect  = cell_rect(col, row)
            inner = rect.inflate(-2, -2)

            if i == 0:
                # Head: brighter colour + eyes
                pygame.draw.rect(surface, C_SNAKE_OUTLINE, inner, border_radius=6)
                pygame.draw.rect(surface, C_SNAKE_HEAD, inner.inflate(-2, -2), border_radius=5)
                self._draw_eyes(surface, rect)
            else:
                pygame.draw.rect(surface, C_SNAKE_OUTLINE, inner, border_radius=4)
                pygame.draw.rect(surface, C_SNAKE_BODY,    inner.inflate(-2, -2), border_radius=3)

    def _draw_eyes(self, surface: pygame.Surface, head_rect: pygame.Rect) -> None:
        """Draw two pupils oriented toward the current direction of travel."""
        cx, cy   = head_rect.centerx, head_rect.centery
        dc, dr   = self.direction
        forward  = (dc * 3, dr * 3)
        sideways = 4

        if dc != 0:   # Horizontal movement → eyes above/below
            e1 = (cx + forward[0], cy + forward[1] - sideways)
            e2 = (cx + forward[0], cy + forward[1] + sideways)
        else:         # Vertical movement → eyes left/right
            e1 = (cx + forward[0] - sideways, cy + forward[1])
            e2 = (cx + forward[0] + sideways, cy + forward[1])

        for eye in (e1, e2):
            pygame.draw.circle(surface, (240, 240, 240), eye, 2)
            pygame.draw.circle(surface, (20,  20,  20),  eye, 1)

    @property
    def head(self) -> tuple[int, int]:
        return self.body[0]

    @property
    def cells(self) -> set[tuple[int, int]]:
        return set(self.body)


# ===========================================================================
# HUD / UI functions
# ===========================================================================
def display_stats(
    surface: pygame.Surface,
    fonts: dict,
    score: int,
    elapsed_seconds: int,
) -> None:
    """
    Render the real-time Score and Timer in the top status bar.

    Layout
    ------
    [SCORE  label]  [score value]       [TIME  label]  [time value]
    Left-aligned                        Right-aligned

    Parameters
    ----------
    surface        : the main pygame display surface
    fonts          : dict of pre-loaded Font objects (keys: 'hud', ...)
    score          : current points total
    elapsed_seconds: integer seconds since the game started
    """
    # Dark HUD background strip
    hud_rect = pygame.Rect(0, 0, WINDOW_WIDTH, HUD_HEIGHT)
    pygame.draw.rect(surface, C_HUD_BG, hud_rect)

    # Bottom separator line
    pygame.draw.line(surface, C_HUD_BORDER, (0, HUD_HEIGHT - 1), (WINDOW_WIDTH, HUD_HEIGHT - 1))

    f = fonts["hud"]

    # --- Left: Score ---
    lbl_score = f.render("SCORE", True, C_SCORE_LABEL)
    val_score = f.render(str(score), True, C_SCORE_VALUE)
    surface.blit(lbl_score, (14, (HUD_HEIGHT - lbl_score.get_height()) // 2))
    surface.blit(val_score, (14 + lbl_score.get_width() + 10,
                              (HUD_HEIGHT - val_score.get_height()) // 2))

    # --- Right: Timer ---
    # Convert elapsed_seconds to MM:SS format
    minutes = elapsed_seconds // 60
    seconds = elapsed_seconds % 60
    time_str = f"{minutes:02d}:{seconds:02d}"

    lbl_time = f.render("TIME", True, C_TIMER_LABEL)
    val_time = f.render(time_str, True, C_TIMER_VALUE)

    # Measure from the right edge
    total_w   = lbl_time.get_width() + 10 + val_time.get_width()
    start_x   = WINDOW_WIDTH - total_w - 14
    mid_y_lbl = (HUD_HEIGHT - lbl_time.get_height()) // 2
    mid_y_val = (HUD_HEIGHT - val_time.get_height()) // 2

    surface.blit(lbl_time, (start_x, mid_y_lbl))
    surface.blit(val_time, (start_x + lbl_time.get_width() + 10, mid_y_val))


# ---------------------------------------------------------------------------

def game_over_screen(
    surface: pygame.Surface,
    fonts: dict,
    score: int,
    elapsed_ms: int,
) -> None:
    """
    Draw a professional Game Over overlay on top of the frozen game frame.

    What is shown
    -------------
    • "GAME OVER"     — large, red, bold
    • Horizontal divider
    • Final Score     — green value
    • Time Survived   — blue value, converted from ms → MM:SS
    • Restart hint    — "Press R to Restart"
    • Quit hint       — "Press Q to Quit"

    Parameters
    ----------
    surface    : the main pygame display surface (game frame already on it)
    fonts      : dict of pre-loaded Font objects (keys: 'title', 'over', 'hint')
    score      : the player's final score
    elapsed_ms : total milliseconds survived (from pygame.time.get_ticks())

    Time conversion
    ---------------
    pygame.time.get_ticks() returns milliseconds (ms).
    Dividing by 1000 gives whole seconds.
    Further dividing by 60 gives minutes; remainder = remaining seconds.
    """
    # ---- Semi-transparent overlay covering the entire window ----
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill(C_OVER_OVERLAY)
    surface.blit(overlay, (0, 0))

    cx = WINDOW_WIDTH  // 2
    cy = WINDOW_HEIGHT // 2

    # ---- "GAME OVER" title ----
    title_surf = fonts["title"].render("GAME OVER", True, C_OVER_TITLE)
    surface.blit(title_surf, title_surf.get_rect(center=(cx, cy - 110)))

    # ---- Horizontal divider ----
    div_y = cy - 68
    pygame.draw.line(surface, C_DIVIDER, (cx - 220, div_y), (cx + 220, div_y), 1)

    # ---- Final Score ----
    lbl_sc   = fonts["over"].render("Final Score", True, C_OVER_TEXT)
    val_sc   = fonts["over"].render(str(score),    True, C_OVER_SCORE)
    surface.blit(lbl_sc, lbl_sc.get_rect(center=(cx, cy - 38)))
    surface.blit(val_sc, val_sc.get_rect(center=(cx, cy +  0)))

    # ---- Time Survived ----
    #  elapsed_ms  (milliseconds) → elapsed_seconds (whole seconds)
    elapsed_seconds = elapsed_ms // 1000          # ms ÷ 1000 = seconds
    minutes         = elapsed_seconds // 60       # whole minutes
    seconds         = elapsed_seconds % 60        # remaining seconds
    time_str        = f"{minutes:02d}:{seconds:02d}"

    lbl_tm  = fonts["over"].render("Time Survived", True, C_OVER_TEXT)
    val_tm  = fonts["over"].render(time_str,        True, C_OVER_TIME)
    surface.blit(lbl_tm, lbl_tm.get_rect(center=(cx, cy + 46)))
    surface.blit(val_tm, val_tm.get_rect(center=(cx, cy + 82)))

    # ---- Second divider ----
    div2_y = cy + 108
    pygame.draw.line(surface, C_DIVIDER, (cx - 220, div2_y), (cx + 220, div2_y), 1)

    # ---- Key hints ----
    hint_r = fonts["hint"].render("Press  R  to Restart", True, C_OVER_RESTART)
    hint_q = fonts["hint"].render("Press  Q  to Quit",    True, C_OVER_QUIT)
    surface.blit(hint_r, hint_r.get_rect(center=(cx, cy + 135)))
    surface.blit(hint_q, hint_q.get_rect(center=(cx, cy + 162)))


# ===========================================================================
# Grid background
# ===========================================================================
def draw_background(surface: pygame.Surface) -> None:
    """Fill the play area and draw faint grid lines."""
    play_rect = pygame.Rect(0, PLAY_TOP, WINDOW_WIDTH, WINDOW_HEIGHT - PLAY_TOP)
    pygame.draw.rect(surface, C_BG, play_rect)

    for col in range(GRID_COLS + 1):
        x = col * CELL_SIZE
        pygame.draw.line(surface, C_GRID, (x, PLAY_TOP), (x, WINDOW_HEIGHT))
    play_rows = (WINDOW_HEIGHT - PLAY_TOP) // CELL_SIZE
    for row in range(play_rows + 1):
        y = row * CELL_SIZE + PLAY_TOP
        pygame.draw.line(surface, C_GRID, (0, y), (WINDOW_WIDTH, y))


# ===========================================================================
# Main Game
# ===========================================================================
def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Snake  |  Arrow Keys to Play")
    clock = pygame.time.Clock()

    # ---- Pre-load fonts (done once for performance) ----
    fonts = {
        "hud"  : pygame.font.SysFont("consolas", 17, bold=True),
        "title": pygame.font.SysFont("consolas", 54, bold=True),
        "over" : pygame.font.SysFont("consolas", 22, bold=False),
        "hint" : pygame.font.SysFont("consolas", 17, bold=True),
    }

    # ---- Game objects ----
    snake = Snake()
    food  = Food()
    food.spawn(snake.cells)

    # ---- State ----
    score: int  = 0
    game_over   = False

    # Record the moment the game begins.
    # pygame.time.get_ticks() returns milliseconds since pygame.init().
    start_ticks: int = pygame.time.get_ticks()
    final_ms: int    = 0     # Will be frozen the moment the game ends

    # ===========================================================================
    # Main Loop
    # ===========================================================================
    while True:
        # ---- Event handling ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if not game_over:
                    # Direction controls — only active while game is running
                    if event.key == pygame.K_UP:
                        snake.queue_direction(DIR_UP)
                    elif event.key == pygame.K_DOWN:
                        snake.queue_direction(DIR_DOWN)
                    elif event.key == pygame.K_LEFT:
                        snake.queue_direction(DIR_LEFT)
                    elif event.key == pygame.K_RIGHT:
                        snake.queue_direction(DIR_RIGHT)
                else:
                    # Game Over screen controls
                    if event.key == pygame.K_r:
                        # Full reset — re-run main() to get a clean slate
                        main()
                        return
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()

        # ---- Update (only when alive) ----
        if not game_over:
            snake.move()

            if not snake.alive:
                # Snake just died — freeze the timer right now
                final_ms  = pygame.time.get_ticks() - start_ticks
                game_over = True

            elif snake.head == food.position:
                # Snake ate food
                score     += SCORE_STEP
                snake.grew = True
                food.spawn(snake.cells)

        # ---- Calculate elapsed time ----
        # pygame.time.get_ticks() gives current ms from program start.
        # Subtracting start_ticks isolates only the current game's duration.
        # Integer division by 1000 converts ms → whole seconds for display.
        if not game_over:
            elapsed_ms      = pygame.time.get_ticks() - start_ticks
        # else: elapsed_ms stays frozen at final_ms (set above on death)

        elapsed_seconds = (final_ms if game_over else elapsed_ms) // 1000

        # ---- Render ----
        draw_background(screen)
        food.draw(screen)
        snake.draw(screen)

        # HUD: score top-left, timer top-right — drawn last so they sit on top
        display_stats(screen, fonts, score, elapsed_seconds)

        # Game Over overlay — drawn over everything when triggered
        if game_over:
            game_over_screen(screen, fonts, score, final_ms)

        pygame.display.flip()
        clock.tick(FPS)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
