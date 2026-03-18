# PyShip — Battleship

A retro-styled Battleship game built with Python and Pygame. Features CRT scanlines, phosphor glow effects, procedural sound, and a classic terminal-aesthetic UI.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `1-5` | Select ship type (placement) |
| `R` | Rotate ship orientation |
| `Enter` | Confirm placement / Fire |
| `A-J` | Select column |
| `1-0` | Select row |
| `F11` | Toggle fullscreen |
| `ESC` | Return to title |

## Architecture

```
src/
  board/       — Grid, ship, placement logic
  game/        — State, engine, turn management
  ui/          — Renderer, sound effects
main.py        — Entry point
```

Built on python 3.14.