"""Retro-styled UI renderer."""

import pygame

from src.game.engine import Engine
from src.game.state import CellState, GameState, Phase


class Renderer:
    WIDTH = 800
    HEIGHT = 700
    CELL_SIZE = 36
    GRID_OFFSET_X = 50
    GRID_OFFSET_Y = 120

    # Retro palette
    BG_COLOR = (10, 10, 20)
    GRID_BG = (20, 30, 20)
    GRID_LINE = (60, 90, 60)
    GRID_LINE_BRIGHT = (80, 140, 80)
    WATER_COLOR = (30, 50, 80)
    SHIP_COLOR = (100, 130, 100)
    HIT_COLOR = (220, 60, 40)
    MISS_COLOR = (60, 80, 120)
    SUNK_COLOR = (180, 40, 30)
    TEXT_COLOR = (180, 220, 160)
    TEXT_DIM = (100, 150, 90)
    ACCENT = (220, 200, 80)
    ENEMY_CURSOR = (220, 200, 80, 100)

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.font_large: pygame.Surface
        self.font_medium: pygame.Surface
        self.font_small: pygame.Surface
        self._init_fonts()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("PyShip — Battleship")
        self._init_fonts()

    def _init_fonts(self) -> None:
        try:
            # Try to load a pixel/retro font
            pygame.font.init()
            self.font_large = pygame.font.SysFont("Courier New", 48, bold=True)
            self.font_medium = pygame.font.SysFont("Courier New", 24, bold=True)
            self.font_small = pygame.font.SysFont("Courier New", 16, bold=False)
        except Exception:
            pygame.font.init()
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)

    def _blit_text(
        self, surface: pygame.Surface, text: str, x: int, y: int, color: tuple[int, int, int]
    ) -> None:
        surf = self.font_small.render(text, False, color)
        surface.blit(surf, (x, y))

    def _draw_grid(
        self, surface: pygame.Surface, grid, offset_x: int, offset_y: int,
        show_ships: bool = False, title: str = ""
    ) -> None:
        gs = self.CELL_SIZE
        size = grid.size

        # Title
        if title:
            self._blit_text(surface, title, offset_x, offset_y - 30, self.TEXT_COLOR)

        # Column labels (A-J)
        for c in range(size):
            lbl = chr(ord("A") + c)
            surf = self.font_small.render(lbl, False, self.TEXT_DIM)
            surface.blit(surf, (offset_x + c * gs + gs // 2 - surf.get_width() // 2, offset_y - 20))

        # Row labels (1-10)
        for r in range(size):
            lbl = str(r + 1)
            surf = self.font_small.render(lbl, False, self.TEXT_DIM)
            surface.blit(surf, (offset_x - 25, offset_y + r * gs + gs // 2 - surf.get_height() // 2))

        # Grid background
        grid_surf = pygame.Surface((size * gs, size * gs), pygame.SRCALPHA)
        grid_surf.fill((20, 25, 20, 220))
        surface.blit(grid_surf, (offset_x, offset_y))

        # Grid lines
        for i in range(size + 1):
            pygame.draw.line(
                surface, self.GRID_LINE,
                (offset_x + i * gs, offset_y),
                (offset_x + i * gs, offset_y + size * gs), 1
            )
            pygame.draw.line(
                surface, self.GRID_LINE,
                (offset_x, offset_y + i * gs),
                (offset_x + size * gs, offset_y + i * gs), 1
            )

        # Cells
        for row in range(size):
            for col in range(size):
                cell = grid.cells[row][col]
                cx = offset_x + col * gs + 2
                cy = offset_y + row * gs + 2
                cw = gs - 4
                ch = gs - 4

                if cell == CellState.SHIP and show_ships:
                    pygame.draw.rect(surface, self.SHIP_COLOR, (cx, cy, cw, ch), 0)
                elif cell == CellState.HIT:
                    self._draw_hit(surface, cx, cy, cw, ch)
                elif cell == CellState.MISS:
                    self._draw_miss(surface, cx, cy, cw, ch)
                elif cell == CellState.SUNK:
                    pygame.draw.rect(surface, self.SUNK_COLOR, (cx, cy, cw, ch), 0)
                    self._draw_hit(surface, cx, cy, cw, ch)

    def _draw_hit(self, surface: pygame.Surface, x: int, y: int, w: int, h: int) -> None:
        cx, cy = x + w // 2, y + h // 2
        r = min(w, h) // 3
        pygame.draw.circle(surface, self.HIT_COLOR, (cx, cy), r)
        pygame.draw.circle(surface, (255, 180, 160), (cx - r // 3, cy - r // 3), r // 3)

    def _draw_miss(self, surface: pygame.Surface, x: int, y: int, w: int, h: int) -> None:
        cx, cy = x + w // 2, y + h // 2
        r = min(w, h) // 4
        pygame.draw.circle(surface, self.MISS_COLOR, (cx, cy), r)

    def _draw_scanlines(self, surface: pygame.Surface) -> None:
        for y in range(0, self.HEIGHT, 3):
            pygame.draw.line(surface, (0, 0, 0, 40), (0, y), (self.WIDTH, y))

    def _draw_vignette(self, surface: pygame.Surface) -> None:
        for i in range(60):
            alpha = int(80 * (i / 60))
            color = (0, 0, 0, alpha)
            pygame.draw.rect(surface, (0, 0, 0, alpha), (i, i, self.WIDTH - 2 * i, self.HEIGHT - 2 * i), 1)

    def _draw_title_screen(self, surface: pygame.Surface) -> None:
        # Title
        title_surf = self.font_large.render("PyShip", False, self.ACCENT)
        title_rect = title_surf.get_rect(center=(self.WIDTH // 2, 180))
        surface.blit(title_surf, title_rect)

        # Subtitle
        sub = self.font_medium.render("BATTLESHIP", False, self.TEXT_COLOR)
        sub_rect = sub.get_rect(center=(self.WIDTH // 2, 240))
        surface.blit(sub, sub_rect)

        # Blinking prompt
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            prompt = self.font_small.render("PRESS ENTER TO START", False, self.TEXT_DIM)
            prompt_rect = prompt.get_rect(center=(self.WIDTH // 2, 380))
            surface.blit(prompt, prompt_rect)

        # Controls
        controls = [
            "CONTROLS:",
            "A-J / 1-0  — select column",
            "R  — rotate ship",
            "ENTER — confirm",
            "ESC  — back to title",
        ]
        y = 480
        for line in controls:
            s = self.font_small.render(line, False, self.TEXT_DIM)
            r = s.get_rect(center=(self.WIDTH // 2, y))
            surface.blit(s, r)
            y += 24

    def _draw_placement_phase(self, surface: pygame.Surface) -> None:
        # Title bar
        title = self.font_medium.render("DEPLOY YOUR FLEET", False, self.ACCENT)
        surface.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 20))

        # Ships to place
        ships_info = [
            ("1 CARRIER     [=====]", ShipType.CARRIER),
            ("2 BATTLESHIP  [====]", ShipType.BATTLESHIP),
            ("3 CRUISER     [===]", ShipType.CRUISER),
            ("4 SUBMARINE   [===]", ShipType.SUBMARINE),
            ("5 DESTROYER   [==]", ShipType.DESTROYER),
        ]
        placed = {s[1] for _, s in self.engine.player_grid.ships}
        y = 60
        for label, st in ships_info:
            placed_flag = "[PLACED]" if st in placed else ""
            color = self.TEXT_DIM if st in placed else (
                self.ACCENT if self.engine.state.selected_ship == st else self.TEXT_COLOR
            )
            line = f"{label}  {placed_flag}"
            s = self.font_small.render(line, False, color)
            surface.blit(s, (60, y))
            y += 22

        # Player grid
        self._draw_grid(
            surface, self.engine.player_grid,
            self.GRID_OFFSET_X, self.GRID_OFFSET_Y,
            show_ships=True
        )

        # Rotate hint
        rot = "HORIZONTAL" if self.engine.state.placement_horizontal else "VERTICAL"
        hint = self.font_small.render(f"[R] {rot}", False, self.TEXT_DIM)
        surface.blit(hint, (60, 520))

        # Message
        msg = self.engine.state.message
        if msg:
            s = self.font_small.render(msg, False, self.ACCENT)
            surface.blit(s, (60, 560))

    def _draw_battle_phase(self, surface: pygame.Surface) -> None:
        # Title
        phase_name = "YOUR TURN" if self.engine.state.phase == Phase.PLAYER_TURN else "ENEMY TURN"
        color = self.ACCENT if self.engine.state.phase == Phase.PLAYER_TURN else self.HIT_COLOR
        title = self.font_medium.render(phase_name, False, color)
        surface.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 15))

        # Column labels at top
        for c in range(self.engine.GRID_SIZE):
            lbl = chr(ord("A") + c)
            surf = self.font_small.render(lbl, False, self.TEXT_DIM)
            surface.blit(surf, (self.WIDTH // 2 + c * self.CELL_SIZE + self.CELL_SIZE // 2 - surf.get_width() // 2, 52))

        # Row labels
        for r in range(self.engine.GRID_SIZE):
            lbl = str(r + 1)
            surf = self.font_small.render(lbl, False, self.TEXT_DIM)
            surface.blit(surf, (self.WIDTH // 2 - 20, 60 + r * self.CELL_SIZE + self.CELL_SIZE // 2 - surf.get_height() // 2))

        # Enemy grid (top-right)
        self._draw_grid(
            surface, self.engine.enemy_grid,
            self.WIDTH // 2 + 10, 65,
            show_ships=False,
            title="ENEMY WATERS"
        )

        # Player grid label
        lbl = self.font_small.render("YOUR FLEET", False, self.TEXT_DIM)
        surface.blit(lbl, (60, 65))

        # Player grid (left)
        self._draw_grid(
            surface, self.engine.player_grid,
            60, 85,
            show_ships=True
        )

        # Message bar
        msg = self.engine.state.message or "Fire at enemy waters!"
        s = self.font_small.render(msg, False, self.TEXT_COLOR)
        surface.blit(s, (60, 500))

        # Controls hint
        hint = "A-J: column  |  1-0: row  |  Enter: fire"
        h = self.font_small.render(hint, False, self.TEXT_DIM)
        surface.blit(h, (60, 530))

        # Legend
        items = [
            ("SHIP", self.SHIP_COLOR),
            ("HIT", self.HIT_COLOR),
            ("MISS", self.MISS_COLOR),
            ("SUNK", self.SUNK_COLOR),
        ]
        x = 60
        for lbl, col in items:
            pygame.draw.rect(surface, col, (x, 560, 14, 14))
            s = self.font_small.render(lbl, False, self.TEXT_DIM)
            surface.blit(s, (x + 20, 559))
            x += 90

    def _draw_game_over_screen(self, surface: pygame.Surface) -> None:
        win = self.engine.state.outcome.value if self.engine.state.outcome else None

        if win == 1:  # PLAYER_WINS
            main = "VICTORY"
            color = self.ACCENT
            sub = "You sank the entire enemy fleet!"
        else:
            main = "DEFEAT"
            color = self.HIT_COLOR
            sub = "Your fleet has been destroyed."

        big = self.font_large.render(main, False, color)
        big_rect = big.get_rect(center=(self.WIDTH // 2, 220))
        surface.blit(big, big_rect)

        s = self.font_medium.render(sub, False, self.TEXT_COLOR)
        s_rect = s.get_rect(center=(self.WIDTH // 2, 290))
        surface.blit(s, s_rect)

        if (pygame.time.get_ticks() // 500) % 2 == 0:
            prompt = self.font_small.render("PRESS ENTER TO RETURN", False, self.TEXT_DIM)
            prompt_rect = prompt.get_rect(center=(self.WIDTH // 2, 400))
            surface.blit(prompt, prompt_rect)

    def draw(self) -> None:
        self.screen.fill(self.BG_COLOR)

        phase = self.engine.state.phase
        if phase == Phase.TITLE:
            self._draw_title_screen(self.screen)
        elif phase == Phase.PLACEMENT:
            self._draw_placement_phase(self.screen)
        elif phase in (Phase.PLAYER_TURN, Phase.ENEMY_TURN):
            self._draw_battle_phase(self.screen)
        elif phase == Phase.GAME_OVER:
            self._draw_battle_phase(self.screen)
            self._draw_game_over_screen(self.screen)

        self._draw_scanlines(self.screen)
        self._draw_vignette(self.screen)
