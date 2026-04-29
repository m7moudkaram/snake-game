"""
Snake Game — main.py
=====================
A complete Pygame Snake game featuring:
  • Intro Screen      (title, team credit, press S to start)
  • Real-time Score   (+10 per food eaten)
  • Live Timer        (elapsed seconds since game start)
  • Professional Game Over screen with final stats + restart/quit

Controls on Intro    : S → Start
Controls during game : Arrow Keys
Controls on Game Over: R → Restart  |  Q → Quit

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
PLAY_TOP   = HUD_HEIGHT                 # Playable area starts below the HUD

FPS        = 12   # Base snake speed (frames per second)
SCORE_STEP = 10   # Points awarded per food item

# ---------------------------------------------------------------------------
# Colour Palette
# ---------------------------------------------------------------------------
C_BG            = (10,  12,  20)
C_GRID          = (22,  26,  42)
C_HUD_BG        = (6,   8,  15)
C_HUD_BORDER    = (35,  40,  65)

C_SNAKE_HEAD    = (60,  230, 120)
C_SNAKE_BODY    = (34,  160,  85)
C_SNAKE_OUTLINE = (18,   90,  48)

C_FOOD          = (235,  75,  75)
C_FOOD_SHINE    = (255, 160, 160)

C_SCORE_LABEL   = (160, 165, 185)
C_SCORE_VALUE   = (80,  220, 140)
C_TIMER_LABEL   = (160, 165, 185)
C_TIMER_VALUE   = (100, 185, 255)

C_OVER_OVERLAY  = (0, 0, 0, 185)
C_OVER_TITLE    = (235,  75,  75)
C_OVER_TEXT     = (200, 205, 220)
C_OVER_SCORE    = (80,  220, 140)
C_OVER_TIME     = (100, 185, 255)
C_OVER_RESTART  = (80,  220, 140)
C_OVER_QUIT     = (235,  75,  75)
C_DIVIDER       = (50,   55,  85)

# Intro screen specific colours
C_INTRO_TITLE   = (60,  230, 120)   # Bold green  — "Snake Game"
C_INTRO_CREDIT  = (160, 165, 185)   # Muted grey  — "Developed by"
C_INTRO_TEAM    = (100, 185, 255)   # Blue accent — "Greenland Team"
C_INTRO_PRESS   = (200, 205, 220)   # White-ish   — "Press  to Start"
C_INTRO_KEY     = (60,  230, 120)   # Green       — the "S" key letter

# Direction vectors (delta-col, delta-row)
DIR_UP    = ( 0, -1)
DIR_DOWN  = ( 0,  1)
DIR_LEFT  = (-1,  0)
DIR_RIGHT = ( 1,  0)


# ===========================================================================
# Utility — convert grid cell coordinates to a pixel Rect
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
# Food — random placement and drawing
# ===========================================================================
class Food:
    """Manages the food pellet: random placement and circle rendering."""

    def __init__(self) -> None:
        self.col = 0
        self.row = 0

    def spawn(self, occupied: set[tuple[int, int]]) -> None:
        """Re-roll until a cell not occupied by the snake is found."""
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
# Snake — body list, movement, collision detection, and rendering
# ===========================================================================
class Snake:
    """
    Represents the player snake.
    body[0] is always the head; body grows toward the tail end.
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

    def queue_direction(self, new_dir: tuple[int, int]) -> None:
        """Buffer a direction change; prevents instant 180-degree reversal."""
        opposite = (-new_dir[0], -new_dir[1])
        if new_dir != opposite:
            self._queued_dir = new_dir

    def move(self) -> None:
        """Advance head by one cell; check wall and self-collision."""
        self.direction = self._queued_dir
        head_col, head_row = self.body[0]
        dc, dr   = self.direction
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
            self.body.pop()   # Normal move — remove tail
        else:
            self.grew = False  # Growth tick — keep tail

    def draw(self, surface: pygame.Surface) -> None:
        for i, (col, row) in enumerate(self.body):
            rect  = cell_rect(col, row)
            inner = rect.inflate(-2, -2)
            if i == 0:
                # Head: brighter fill + directional eyes
                pygame.draw.rect(surface, C_SNAKE_OUTLINE, inner, border_radius=6)
                pygame.draw.rect(surface, C_SNAKE_HEAD, inner.inflate(-2, -2), border_radius=5)
                self._draw_eyes(surface, rect)
            else:
                pygame.draw.rect(surface, C_SNAKE_OUTLINE, inner, border_radius=4)
                pygame.draw.rect(surface, C_SNAKE_BODY,    inner.inflate(-2, -2), border_radius=3)

    def _draw_eyes(self, surface: pygame.Surface, head_rect: pygame.Rect) -> None:
        """Draw two small pupils oriented in the current direction of travel."""
        cx, cy   = head_rect.centerx, head_rect.centery
        dc, dr   = self.direction
        forward  = (dc * 3, dr * 3)
        sideways = 4
        if dc != 0:   # Horizontal movement → eyes above/below centre
            e1 = (cx + forward[0], cy + forward[1] - sideways)
            e2 = (cx + forward[0], cy + forward[1] + sideways)
        else:         # Vertical movement → eyes left/right of centre
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
# INTRO SCREEN — shown once when the game launches (and on restart)
# ===========================================================================
def show_intro(surface: pygame.Surface, clock: pygame.time.Clock) -> None:
    """
    Display the title screen and block until the player presses S.

    Visual layout (vertically centred on the window)
    -------------------------------------------------
      ─────────────── divider ───────────────
           Snake Game          ← large, bold, GREEN
         Developed by
          Greenland Team       ← blue accent
      ─────────────── divider ───────────────
         Press  S  to Start    ← pulsing hint

    The "Press S to Start" line pulses (alpha fade) to attract attention.
    The "S" key is rendered in green to match the title colour.
    """
    # ---- Intro-specific fonts ----
    font_title  = pygame.font.SysFont("consolas", 64, bold=True)
    font_credit = pygame.font.SysFont("consolas", 20, bold=False)
    font_team   = pygame.font.SysFont("consolas", 22, bold=True)
    font_press  = pygame.font.SysFont("consolas", 22, bold=True)

    cx = WINDOW_WIDTH  // 2
    cy = WINDOW_HEIGHT // 2

    # Pre-render static text surfaces
    title_surf  = font_title.render("Snake Game",     True, C_INTRO_TITLE)
    credit_surf = font_credit.render("Developed by",  True, C_INTRO_CREDIT)
    team_surf   = font_team.render("Greenland Team",  True, C_INTRO_TEAM)

    # "Press S to Start" — three segments so "S" can be a different colour
    seg_pre  = font_press.render("Press ",     True, C_INTRO_PRESS)
    seg_key  = font_press.render("S",          True, C_INTRO_KEY)
    seg_post = font_press.render(" to Start",  True, C_INTRO_PRESS)

    # Total width of the full hint line (used to centre it)
    hint_total_w = seg_pre.get_width() + seg_key.get_width() + seg_post.get_width()
    hint_x       = cx - hint_total_w // 2
    hint_y       = cy + 100

    # Pulse state — oscillates alpha between 60 and 255
    pulse_alpha = 255
    pulse_dir   = -3     # negative = fading out

    # ---- Intro event loop ----
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                return    # S pressed → exit intro, game begins

        # Background + faint grid (matches the game's look)
        surface.fill(C_BG)
        for col in range(GRID_COLS + 1):
            pygame.draw.line(surface, C_GRID,
                             (col * CELL_SIZE, 0),
                             (col * CELL_SIZE, WINDOW_HEIGHT))
        for row in range(GRID_ROWS + 1):
            pygame.draw.line(surface, C_GRID,
                             (0, row * CELL_SIZE),
                             (WINDOW_WIDTH, row * CELL_SIZE))

        # Top divider
        pygame.draw.line(surface, C_DIVIDER,
                         (cx - 250, cy - 100), (cx + 250, cy - 100), 1)

        # "Snake Game" title — bold, green, centred
        surface.blit(title_surf, title_surf.get_rect(center=(cx, cy - 44)))

        # "Developed by" — small, muted
        surface.blit(credit_surf, credit_surf.get_rect(center=(cx, cy + 18)))

        # "Greenland Team" — slightly larger, blue accent
        surface.blit(team_surf, team_surf.get_rect(center=(cx, cy + 46)))

        # Bottom divider
        pygame.draw.line(surface, C_DIVIDER,
                         (cx - 250, cy + 74), (cx + 250, cy + 74), 1)

        # Pulsing "Press S to Start"
        seg_pre.set_alpha(pulse_alpha)
        seg_key.set_alpha(pulse_alpha)
        seg_post.set_alpha(pulse_alpha)

        surface.blit(seg_pre,  (hint_x, hint_y))
        surface.blit(seg_key,  (hint_x + seg_pre.get_width(), hint_y))
        surface.blit(seg_post, (hint_x + seg_pre.get_width() + seg_key.get_width(), hint_y))

        # Update pulse — bounce alpha between 60 and 255
        pulse_alpha += pulse_dir
        if pulse_alpha <= 60:
            pulse_dir = +3
        elif pulse_alpha >= 255:
            pulse_dir = -3

        pygame.display.flip()
        clock.tick(60)   # 60 fps for smooth pulse animation


# ===========================================================================
# HUD — display_stats(): Score (top-left) and Timer (top-right)
# ===========================================================================
def display_stats(
    surface: pygame.Surface,
    fonts: dict,
    score: int,
    elapsed_seconds: int,
) -> None:
    """
    Draw the top status bar with real-time Score and Timer.

    Time format: MM:SS
      minutes = elapsed_seconds // 60
      seconds = elapsed_seconds % 60
    """
    # HUD background strip
    pygame.draw.rect(surface, C_HUD_BG, pygame.Rect(0, 0, WINDOW_WIDTH, HUD_HEIGHT))
    pygame.draw.line(surface, C_HUD_BORDER,
                     (0, HUD_HEIGHT - 1), (WINDOW_WIDTH, HUD_HEIGHT - 1))

    f = fonts["hud"]

    # Left — Score label + value
    lbl_score = f.render("SCORE", True, C_SCORE_LABEL)
    val_score = f.render(str(score), True, C_SCORE_VALUE)
    surface.blit(lbl_score, (14, (HUD_HEIGHT - lbl_score.get_height()) // 2))
    surface.blit(val_score, (14 + lbl_score.get_width() + 10,
                              (HUD_HEIGHT - val_score.get_height()) // 2))

    # Right — Timer label + MM:SS value
    minutes  = elapsed_seconds // 60
    seconds  = elapsed_seconds % 60
    time_str = f"{minutes:02d}:{seconds:02d}"

    lbl_time = f.render("TIME", True, C_TIMER_LABEL)
    val_time = f.render(time_str,  True, C_TIMER_VALUE)
    total_w  = lbl_time.get_width() + 10 + val_time.get_width()
    start_x  = WINDOW_WIDTH - total_w - 14

    surface.blit(lbl_time, (start_x, (HUD_HEIGHT - lbl_time.get_height()) // 2))
    surface.blit(val_time, (start_x + lbl_time.get_width() + 10,
                             (HUD_HEIGHT - val_time.get_height()) // 2))


# ===========================================================================
# Game Over overlay — game_over_screen()
# ===========================================================================
def game_over_screen(
    surface: pygame.Surface,
    fonts: dict,
    score: int,
    elapsed_ms: int,
) -> None:
    """
    Semi-transparent overlay with final score, time survived, and key hints.

    Time conversion (ms → MM:SS):
      elapsed_seconds = elapsed_ms // 1000    (ms ÷ 1000 = seconds)
      minutes         = elapsed_seconds // 60
      seconds         = elapsed_seconds % 60
    """
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill(C_OVER_OVERLAY)
    surface.blit(overlay, (0, 0))

    cx = WINDOW_WIDTH  // 2
    cy = WINDOW_HEIGHT // 2

    # "GAME OVER" — large red title
    title_surf = fonts["title"].render("GAME OVER", True, C_OVER_TITLE)
    surface.blit(title_surf, title_surf.get_rect(center=(cx, cy - 110)))

    pygame.draw.line(surface, C_DIVIDER, (cx - 220, cy - 68), (cx + 220, cy - 68), 1)

    # Final Score
    lbl_sc = fonts["over"].render("Final Score", True, C_OVER_TEXT)
    val_sc = fonts["over"].render(str(score),    True, C_OVER_SCORE)
    surface.blit(lbl_sc, lbl_sc.get_rect(center=(cx, cy - 38)))
    surface.blit(val_sc, val_sc.get_rect(center=(cx, cy +  0)))

    # Time Survived
    elapsed_seconds = elapsed_ms // 1000
    minutes         = elapsed_seconds // 60
    seconds         = elapsed_seconds % 60
    time_str        = f"{minutes:02d}:{seconds:02d}"

    lbl_tm = fonts["over"].render("Time Survived", True, C_OVER_TEXT)
    val_tm = fonts["over"].render(time_str,        True, C_OVER_TIME)
    surface.blit(lbl_tm, lbl_tm.get_rect(center=(cx, cy + 46)))
    surface.blit(val_tm, val_tm.get_rect(center=(cx, cy + 82)))

    pygame.draw.line(surface, C_DIVIDER, (cx - 220, cy + 108), (cx + 220, cy + 108), 1)

    # Key hints
    hint_r = fonts["hint"].render("Press  R  to Restart", True, C_OVER_RESTART)
    hint_q = fonts["hint"].render("Press  Q  to Quit",    True, C_OVER_QUIT)
    surface.blit(hint_r, hint_r.get_rect(center=(cx, cy + 135)))
    surface.blit(hint_q, hint_q.get_rect(center=(cx, cy + 162)))


# ===========================================================================
# Grid background
# ===========================================================================
def draw_background(surface: pygame.Surface) -> None:
    """Dark background + faint grid lines in the play area."""
    pygame.draw.rect(surface, C_BG,
                     pygame.Rect(0, PLAY_TOP, WINDOW_WIDTH, WINDOW_HEIGHT - PLAY_TOP))
    for col in range(GRID_COLS + 1):
        pygame.draw.line(surface, C_GRID,
                         (col * CELL_SIZE, PLAY_TOP),
                         (col * CELL_SIZE, WINDOW_HEIGHT))
    play_rows = (WINDOW_HEIGHT - PLAY_TOP) // CELL_SIZE
    for row in range(play_rows + 1):
        y = row * CELL_SIZE + PLAY_TOP
        pygame.draw.line(surface, C_GRID, (0, y), (WINDOW_WIDTH, y))


# ===========================================================================
# Entry point — init → intro → game loop
# ===========================================================================
def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Snake  |  Greenland Team")
    clock  = pygame.time.Clock()

    # Pre-load fonts used during gameplay (done once for performance)
    fonts = {
        "hud"  : pygame.font.SysFont("consolas", 17, bold=True),
        "title": pygame.font.SysFont("consolas", 54, bold=True),
        "over" : pygame.font.SysFont("consolas", 22, bold=False),
        "hint" : pygame.font.SysFont("consolas", 17, bold=True),
    }

    # ---- Show intro — waits here until player presses S ----
    show_intro(screen, clock)

    # ---- Initialise game objects right after S is pressed ----
    snake = Snake()
    food  = Food()
    food.spawn(snake.cells)

    score: int   = 0
    game_over    = False

    # Record start time in milliseconds.
    # pygame.time.get_ticks() counts ms since pygame.init() was called.
    # Subtracting start_ticks every frame isolates this game session's time.
    start_ticks: int = pygame.time.get_ticks()
    final_ms: int    = 0   # Frozen at the moment of death

    # ---- Main game loop ----
    while True:
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if not game_over:
                    if event.key == pygame.K_UP:
                        snake.queue_direction(DIR_UP)
                    elif event.key == pygame.K_DOWN:
                        snake.queue_direction(DIR_DOWN)
                    elif event.key == pygame.K_LEFT:
                        snake.queue_direction(DIR_LEFT)
                    elif event.key == pygame.K_RIGHT:
                        snake.queue_direction(DIR_RIGHT)
                else:
                    if event.key == pygame.K_r:
                        main()   # Restart — goes back to intro screen
                        return
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()

        # Update
        if not game_over:
            snake.move()

            if not snake.alive:
                # Freeze the timer at the exact death frame
                final_ms  = pygame.time.get_ticks() - start_ticks
                game_over = True

            elif snake.head == food.position:
                score     += SCORE_STEP
                snake.grew = True
                food.spawn(snake.cells)

        # Elapsed time calculation:
        # get_ticks() returns ms → subtract start → divide by 1000 for seconds
        elapsed_ms      = final_ms if game_over else (pygame.time.get_ticks() - start_ticks)
        elapsed_seconds = elapsed_ms // 1000

        # Render
        draw_background(screen)
        food.draw(screen)
        snake.draw(screen)
        display_stats(screen, fonts, score, elapsed_seconds)

        if game_over:
            game_over_screen(screen, fonts, score, final_ms)

        pygame.display.flip()
        clock.tick(FPS)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
