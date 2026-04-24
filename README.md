# PyShip — Retro Battleship

A retro-styled Battleship game built with Python and Pygame. Features CRT scanlines, phosphor glow effects, procedural sound, and a classic terminal-aesthetic UI for a classic feel.

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
| `Arrow Keys` | Move cursor in grid |
| `1-5` | Select ship type to deploy (1 of each required) |
| `R` | Rotate ship orientation (horizontal/vertical) |
| `Enter` | Confirm ship placement / Fire weapon |
| `A-J` | Jump cursor to column |
| `1-0` | Jump cursor to row (0 = row 10) |
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

1. **Deploy** — Select a ship (1=Carrier, 2=Battleship, 3=Cruiser, 4=Submarine, 5=Destroyer). Use the **Arrow Keys** to position the placement preview on your grid, **R** to rotate, and **Enter** to deploy. You must deploy all 5 unique ships.
2. **Battle** — Use the **Arrow Keys** (or A-J/1-0 shortcuts) to move the targeting cursor on the enemy grid, then press **Enter** to fire.
3. **Sink** — The *Enemy Ships* panel tracks your opponent's fleet. Sink all 5 ships before they sink yours!

*Developed on Python 3.14.3*