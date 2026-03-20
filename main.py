"""PyShip - A retro-styled Battleship game."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pygame

from src.game.engine import Engine
from src.game.state import Phase
from src.ui.renderer import Renderer
from src.ui.sound import SoundFX


def main() -> None:
    pygame.init()
    pygame.mixer.init()

    sfx = SoundFX()
    engine = Engine()
    engine.sfx = sfx

    renderer = Renderer(engine)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.VIDEORESIZE:
                renderer.handle_resize()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    renderer._toggle_fullscreen()
                    continue

            engine.handle_event(event)

        engine.update()
        renderer.draw()

    pygame.quit()


if __name__ == "__main__":
    main()
