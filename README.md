# PyShip — Battleship

A retro-styled Battleship game built with Python and Pygame. Features CRT scanlines, phosphor glow effects, procedural sound, and a classic terminal-aesthetic UI.

## Requirements

- Python 3.10+
- Pygame (includes SDL2)
- NumPy (for procedural sound)

**macOS:** SDL2 development libraries required — install via Homebrew first.
**Windows/Linux:** No extra system dependencies — pip handles everything.

## Setup

### macOS

```bash
# Install SDL2 libraries (required for Pygame)
brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf

# Clone and setup
git clone https://github.com/chrisF943/PyShip.git
cd PyShip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows

```bash
# Clone and setup (SDL2 is bundled with pygame wheels)
git clone https://github.com/chrisF943/PyShip.git
cd PyShip
python -m venv .venv
.venv\Scripts\activate.ps1
pip install -r requirements.txt
```

### Linux

```bash
# Install SDL2 development libraries
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

git clone https://github.com/chrisF943/PyShip.git
cd PyShip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
# Activate venv first (macOS/Linux)
source .venv/bin/activate

# Run the game
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `1-5` | Select ship type (placement) |
| `R` | Rotate ship orientation |
| `Enter` | Confirm placement / Fire |
| `A-J` | Select column |
| `1-0` | Select row (0 = row 10) |
| `F11` | Toggle fullscreen |
| `ESC` | Return to title |

## Architecture

```
src/
  board/       — Grid, ship, and placement logic
  game/        — State, engine, turn management
  ui/          — Renderer (CRT effects), procedural sound
main.py        — Entry point
```

## Gameplay

1. **Deploy** — Select a ship (1-5), press Enter to auto-place
2. **Battle** — Use A-J for column, 1-0 for row, Enter to fire
3. **Sink** the enemy fleet before they sink yours
