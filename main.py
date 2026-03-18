"""PyShip - A retro-styled Battleship game."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pygame

from src.game.state import GameState
from src.game.engine import Engine
from src.ui.renderer import Renderer


def main() -> None:
    pygame.init()

    engine = Engine()
    renderer = Renderer(engine)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            engine.handle_event(event)

        engine.update()
        renderer.draw()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
