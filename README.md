# 🐍 Snake Game — Pygame

A clean, feature-rich Snake game built with Python and Pygame.
Includes a real-time score tracker, live timer, smooth grid movement,
and a professional Game Over screen.

---

## 📸 Preview

```
┌─────────────────────────────────────────┐
│  SCORE  80                   TIME 00:42 │  ← HUD Bar
├─────────────────────────────────────────┤
│  · · · · · · · · · · · · · · · · · · · │
│  · · · · · ██████ · · · · · · · · · · · │
│  · · · · · ██████ · · · · · · · · · · · │
│  · · · · · ██HEAD→ · · · · 🔴 · · · · · │
│  · · · · · · · · · · · · · · · · · · · │
└─────────────────────────────────────────┘
```

---

## Features

| Feature | Detail |
|---|---|
| **Scoring** | +10 points every time the snake eats food |
| **Live Timer** | Elapsed time displayed as `MM:SS` in the HUD |
| **Speed Scaling** | Base FPS of 12 — adjustable via constant |
| **Game Over Screen** | Final Score + Time Survived + Restart / Quit prompts |
| **Smooth Rendering** | `clock.tick(FPS)` controls frame rate; no flickering |
| **Collision Detection** | Wall hits and self-collision both trigger Game Over |
| **Anti-reversal** | Snake cannot instantly reverse into itself |
| **Visual Polish** | Rounded segments, directional eyes on head, shine on food |

---

## Project Structure

```
Snake-Game/
│
├── main.py        # Complete game — all logic, classes, and rendering
└── README.md      # This file
```

All game logic lives in a single, well-commented `main.py`:

```
main.py
 ├── Constants & Colour Palette
 ├── cell_rect()          — grid → pixel coordinate helper
 ├── class Food           — spawn, position, draw
 ├── class Snake          — body, movement, collision, draw
 ├── display_stats()      — live HUD (score + timer)
 ├── game_over_screen()   — overlay with final stats + key hints
 ├── draw_background()    — dark grid background
 └── main()               — game loop (event → update → render)
```

---

## Getting Started

### Prerequisites

- Python **3.10+**
- Pygame **2.x**

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/snake-game.git
cd snake-game

# 2. Install the only dependency
pip install pygame

# 3. Run the game
python main.py
```

---

## Controls

| Key | Action |
|---|---|
| `↑` `↓` `←` `→` | Move the snake |
| `R` | Restart (on Game Over screen) |
| `Q` | Quit (on Game Over screen) |

---

## Configuration

All tuneable constants are grouped at the top of `main.py`:

```python
WINDOW_WIDTH  = 800     # Window width  (px)
WINDOW_HEIGHT = 640     # Window height (px)
CELL_SIZE     = 20      # Grid cell size (px)
HUD_HEIGHT    = 40      # Top status bar height (px)
FPS           = 12      # Snake speed — higher = faster
SCORE_STEP    = 10      # Points per food item
```

Change any of these and the rest of the game adapts automatically.

---

## Architecture Notes

### Timer — how `get_ticks()` is used

```python
# At game start:
start_ticks = pygame.time.get_ticks()   # ms since pygame.init()

# Every frame:
elapsed_ms      = pygame.time.get_ticks() - start_ticks  # duration of this game
elapsed_seconds = elapsed_ms // 1000                     # ms ÷ 1000 = seconds
minutes         = elapsed_seconds // 60
seconds         = elapsed_seconds % 60
```

When the snake dies, `final_ms` is frozen immediately so the timer stops on the exact death frame.

### Rendering pipeline (per frame)

```
draw_background()   →   food.draw()   →   snake.draw()
    →   display_stats()   →   [game_over_screen()]   →   pygame.display.flip()
```

---
