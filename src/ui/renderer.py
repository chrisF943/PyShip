"""Retro-styled UI renderer."""

import math
import pygame

from src.game.engine import Engine
from src.game.state import CellState, Phase, ShipType


class Renderer:
    BASE_WIDTH = 900
    BASE_HEIGHT = 700
    CELL_SIZE = 36

    # Retro palette
    BG_COLOR = (8, 8, 16)
    GRID_BG = (15, 22, 15)
    GRID_LINE = (50, 80, 50)
    GRID_LINE_BRIGHT = (80, 140, 80)
    SHIP_COLOR = (90, 120, 90)
    SHIP_BRIGHT = (120, 160, 120)
    HIT_COLOR = (220, 50, 30)
    HIT_BRIGHT = (255, 120, 80)
    MISS_COLOR = (50, 70, 100)
    SUNK_COLOR = (140, 30, 20)
    TEXT_COLOR = (170, 210, 150)
    TEXT_DIM = (80, 120, 75)
    ACCENT = (220, 200, 70)
    CURSOR_COLOR = (220, 200, 70, 80)

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._scale = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self._fullscreen = False
        self._fs_surface: pygame.Surface | None = None
        self._init_fonts()
        self._screen = pygame.display.set_mode(
            (self.BASE_WIDTH, self.BASE_HEIGHT),
            pygame.RESIZABLE
        )
        pygame.display.set_caption("PyShip — Battleship")
        self._clock = pygame.time.Clock()
        self._anim_time = 0.0

        # Cursor position for targeting
        self._cursor_col = 0
        self._cursor_row = 0

        # Generate procedural ship sprites
        self._ship_sprites = self._generate_ship_sprites()

    def _generate_ship_sprites(self) -> dict:
        """Generate pixel-art ship sprites procedurally."""
        sprites = {}
        for ship_type in ShipType:
            size = {
                ShipType.CARRIER: 5,
                ShipType.BATTLESHIP: 4,
                ShipType.CRUISER: 3,
                ShipType.SUBMARINE: 3,
                ShipType.DESTROYER: 2,
            }[ship_type]
            cell = self.CELL_SIZE
            # Create a horizontal ship sprite
            surf = pygame.Surface((size * cell, cell), pygame.SRCALPHA)
            # Hull
            for i in range(size):
                x = i * cell
                # Main hull
                pygame.draw.rect(surf, self.SHIP_COLOR, (x + 2, 4, cell - 4, cell - 8))
                # Highlight on top
                pygame.draw.rect(surf, self.SHIP_BRIGHT, (x + 4, 4, cell - 8, 3))
                # Bow (front)
                if i == 0:
                    pygame.draw.polygon(surf, self.SHIP_BRIGHT, [
                        (x + cell - 4, 4), (x + cell, cell // 2), (x + cell - 4, cell - 4)
                    ])
                # Stern (back)
                if i == size - 1:
                    pygame.draw.polygon(surf, self.SHIP_COLOR, [
                        (x, 4), (x + 4, cell // 2), (x, cell - 4)
                    ])
            sprites[(ship_type, True)] = surf
            # Vertical sprite
            surf_v = pygame.Surface((cell, size * cell), pygame.SRCALPHA)
            for i in range(size):
                y = i * cell
                pygame.draw.rect(surf_v, self.SHIP_COLOR, (4, y + 2, cell - 8, cell - 4))
                pygame.draw.rect(surf_v, self.SHIP_BRIGHT, (4, y + 4, 3, cell - 8))
                if i == 0:
                    pygame.draw.polygon(surf_v, self.SHIP_BRIGHT, [
                        (4, y + cell - 4), (cell // 2, y + cell), (cell - 4, y + cell - 4)
                    ])
                if i == size - 1:
                    pygame.draw.polygon(surf_v, self.SHIP_COLOR, [
                        (4, y), (cell // 2, y + 4), (cell - 4, y)
                    ])
            sprites[(ship_type, False)] = surf_v
        return sprites

    def _init_fonts(self) -> None:
        pygame.font.init()
        self.font_large = pygame.font.SysFont("Courier New", 52, bold=True)
        self.font_medium = pygame.font.SysFont("Courier New", 22, bold=True)
        self.font_small = pygame.font.SysFont("Courier New", 14, bold=False)
        self.font_tiny = pygame.font.SysFont("Courier New", 11, bold=False)

    def _toggle_fullscreen(self) -> None:
        if self._fullscreen:
            pygame.display.set_mode((self.BASE_WIDTH, self.BASE_HEIGHT), pygame.RESIZABLE)
            self._fullscreen = False
        else:
            self._fs_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self._fullscreen = True

    def _blit_text(self, surf: pygame.Surface, text: str, x: int, y: int,
                   color: tuple[int, int, int], center: bool = False) -> None:
        s = self.font_small.render(text, False, color)
        if center:
            r = s.get_rect(center=(x, y))
            surf.blit(s, r)
        else:
            surf.blit(s, (x, y))

    def _draw_cell(self, surf: pygame.Surface, col: int, row: int,
                   cell: CellState, gs: int, ox: int, oy: int,
                   show_ship: bool = False) -> None:
        x = ox + col * gs + 2
        y = oy + row * gs + 2
        w = gs - 4
        h = gs - 4

        if cell == CellState.SHIP and show_ship:
            # Draw water behind ship first
            pygame.draw.rect(surf, (20, 40, 70), (x, y, w, h))
            # Ship pixel
            pygame.draw.rect(surf, self.SHIP_COLOR, (x, y, w, h))
            pygame.draw.rect(surf, self.SHIP_BRIGHT, (x + 2, y + 2, w - 4, 3))
        elif cell == CellState.EMPTY:
            # Water with subtle pattern
            pygame.draw.rect(surf, (18, 35, 65), (x, y, w, h))
            # Water shimmer
            wave = int(math.sin(self._anim_time * 2 + col * 0.5 + row * 0.3) * 2)
            if wave > 0:
                pygame.draw.rect(surf, (25, 50, 80), (x, y + wave, w, 1))
        elif cell == CellState.HIT:
            pygame.draw.rect(surf, (20, 40, 70), (x, y, w, h))
            self._draw_cross(surf, x, y, w, h, self.HIT_COLOR)
        elif cell == CellState.MISS:
            pygame.draw.rect(surf, (18, 35, 65), (x, y, w, h))
            self._draw_miss_marker(surf, x, y, w, h)
        elif cell == CellState.SUNK:
            pygame.draw.rect(surf, (30, 10, 10), (x, y, w, h))
            self._draw_cross(surf, x, y, w, h, self.SUNK_COLOR)

    def _draw_cross(self, surf: pygame.Surface, x: int, y: int, w: int, h: int,
                    color: tuple[int, int, int]) -> None:
        # Animated pulse
        intensity = 0.7 + 0.3 * math.sin(self._anim_time * 6)
        r = int(color[0] * intensity)
        g = int(color[1] * intensity)
        b = int(color[2] * intensity)
        pulse = (r, g, b)
        cx, cy = x + w // 2, y + h // 2
        # Draw X
        thickness = max(2, w // 5)
        pygame.draw.line(surf, pulse, (x + 4, y + 4), (x + w - 4, y + h - 4), thickness)
        pygame.draw.line(surf, pulse, (x + w - 4, y + 4), (x + 4, y + h - 4), thickness)

    def _draw_miss_marker(self, surf: pygame.Surface, x: int, y: int, w: int, h: int) -> None:
        cx, cy = x + w // 2, y + h // 2
        r = w // 4
        pygame.draw.circle(surf, self.MISS_COLOR, (cx, cy), r, 2)
        # Dot in center
        pygame.draw.circle(surf, (70, 90, 120), (cx, cy), 2)

    def _draw_grid(self, surf: pygame.Surface, grid, ox: int, oy: int,
                   show_ships: bool = False, title: str = "") -> None:
        gs = self.CELL_SIZE
        size = grid.size

        if title:
            t = self.font_small.render(title, False, self.TEXT_DIM)
            surf.blit(t, (ox, oy - 22))

        # Column labels
        for c in range(size):
            lbl = chr(ord("A") + c)
            s = self.font_tiny.render(lbl, False, self.TEXT_DIM)
            surf.blit(s, (ox + c * gs + gs // 2 - s.get_width() // 2, oy - 16))

        # Row labels
        for r in range(size):
            lbl = str(r + 1)
            s = self.font_tiny.render(lbl, False, self.TEXT_DIM)
            surf.blit(s, (ox - 18, oy + r * gs + gs // 2 - s.get_height() // 2))

        # Grid background
        bg = pygame.Surface((size * gs, size * gs), pygame.SRCALPHA)
        bg.fill((12, 18, 12, 230))
        surf.blit(bg, (ox, oy))

        # Grid border
        pygame.draw.rect(surf, self.GRID_LINE_BRIGHT, (ox - 1, oy - 1, size * gs + 2, size * gs + 2), 1)

        # Grid lines
        for i in range(1, size):
            pygame.draw.line(surf, self.GRID_LINE,
                             (ox + i * gs, oy), (ox + i * gs, oy + size * gs))
            pygame.draw.line(surf, self.GRID_LINE,
                             (ox, oy + i * gs), (ox + size * gs, oy + i * gs))

        # Cells
        for row in range(size):
            for col in range(size):
                self._draw_cell(surf, col, row, grid.cells[row][col], gs, ox, oy, show_ships)

    def _draw_cursor(self, surf: pygame.Surface, col: int, row: int,
                     gs: int, ox: int, oy: int, is_enemy: bool) -> None:
        """Draw targeting cursor on enemy grid during player turn."""
        if not is_enemy or self.engine.state.phase != Phase.PLAYER_TURN:
            return
        pulse = 0.5 + 0.5 * math.sin(self._anim_time * 8)
        alpha = int(100 + 100 * pulse)
        x = ox + col * gs
        y = oy + row * gs
        rect = pygame.Surface((gs, gs), pygame.SRCALPHA)
        rect.fill((220, 200, 70, alpha // 3))
        surf.blit(rect, (x, y))
        # Corner brackets
        blen = gs // 4
        color = (220, 200, 70, alpha)
        for bx, by in [(x, y), (x + gs - blen, y),
                       (x, y + gs - blen), (x + gs - blen, y + gs - blen)]:
            pass  # corners drawn below

        surf.blit(rect, (x, y))

    def _draw_fire_effect(self, surf: pygame.Surface) -> None:
        """Draw explosion/fire animation."""
        if not self.engine._fire_animation:
            return
        col, row, timer = self.engine._fire_animation
        # Enemy grid position (offset from center-right)
        gs = self.CELL_SIZE
        ox = self.BASE_WIDTH // 2 + 20
        oy = 60
        x = ox + col * gs + gs // 2
        y = oy + row * gs + gs // 2
        # Expanding ring
        radius = int((0.5 - timer) * gs * 2)
        if radius > 0:
            alpha = int(timer * 2 * 200)
            ring = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 150, 50, alpha), (radius + 2, radius + 2), radius, 2)
            surf.blit(ring, (x - radius - 2, y - radius - 2))

    def _draw_scanlines(self, surf: pygame.Surface) -> None:
        for y in range(0, self.BASE_HEIGHT, 3):
            pygame.draw.line(surf, (0, 0, 0, 35), (0, y), (self.BASE_WIDTH, y))

    def _draw_vignette(self, surf: pygame.Surface) -> None:
        for i in range(80):
            alpha = int(100 * (i / 80) ** 1.5)
            pygame.draw.rect(surf, (0, 0, 0, alpha),
                             (i, i, self.BASE_WIDTH - 2 * i, self.BASE_HEIGHT - 2 * i), 1)

    def _draw_phosphor_glow(self, surf: pygame.Surface) -> None:
        """Add subtle green phosphor glow overlay."""
        glow = pygame.Surface((self.BASE_WIDTH, self.BASE_HEIGHT), pygame.SRCALPHA)
        for x in range(0, self.BASE_WIDTH, 40):
            for y in range(0, self.BASE_HEIGHT, 40):
                pygame.draw.circle(glow, (20, 60, 20, 8), (x, y), 20)
        surf.blit(glow, (0, 0))

    def _draw_title_screen(self, surf: pygame.Surface) -> None:
        # ASCII art title
        title_lines = [
            "  ____  ___  _   __  ____  ___  __ _  ____  _  _",
            " (  __)/ __)/ ) (  )(  __)/ __)(  / )(  __)( \\/ )",
            "  ) _)( (__ / \\/ \\ )(  ) _( (__  )  (  ) _) / \\/ ",
            " (__)  \\___)\\_)(_/(____)(___)(___)(__)(____)(_)\\_)",
        ]
        t = 0.0
        for i, line in enumerate(title_lines):
            x = self.BASE_WIDTH // 2 - len(line) * 5
            y = 100 + i * 22
            # Subtle wave
            wave_y = y + int(math.sin(t + i * 0.5) * 3)
            s = self.font_small.render(line, False, self.ACCENT)
            r = s.get_rect(center=(self.BASE_WIDTH // 2, wave_y + 14))
            surf.blit(s, r)

        # Subtitle
        sub = self.font_medium.render("B A T T L E S H I P", False, self.TEXT_COLOR)
        r = sub.get_rect(center=(self.BASE_WIDTH // 2, 240))
        surf.blit(sub, r)

        # Blinking prompt
        if (pygame.time.get_ticks() // 600) % 2 == 0:
            p = self.font_small.render(">> PRESS ENTER TO DEPLOY <<", False, self.ACCENT)
            r = p.get_rect(center=(self.BASE_WIDTH // 2, 360))
            surf.blit(p, r)

        # Credits line
        c = self.font_tiny.render("PyShip — A Retro Battleship Experience", False, self.TEXT_DIM)
        r = c.get_rect(center=(self.BASE_WIDTH // 2, 420))
        surf.blit(c, r)

        # Controls panel
        panel_lines = [
            "━━━ CONTROLS ━━━",
            "A-J  COLUMN    1-0  ROW",
            "ENTER  FIRE     R  ROTATE",
            "F11  FULLSCREEN  ESC  MENU",
        ]
        px = self.BASE_WIDTH // 2 - 120
        py = 470
        for line in panel_lines:
            s = self.font_tiny.render(line, False, self.TEXT_DIM)
            surf.blit(s, (px, py))
            py += 16

    def _draw_placement_phase(self, surf: pygame.Surface) -> None:
        # Header
        h = self.font_medium.render("◈ DEPLOY YOUR FLEET ◈", False, self.ACCENT)
        r = h.get_rect(center=(self.BASE_WIDTH // 2, 28))
        surf.blit(h, r)

        # Ship list
        ships_info = [
            ("[1] CARRIER     — 5 cells", ShipType.CARRIER),
            ("[2] BATTLESHIP  — 4 cells", ShipType.BATTLESHIP),
            ("[3] CRUISER     — 3 cells", ShipType.CRUISER),
            ("[4] SUBMARINE   — 3 cells", ShipType.SUBMARINE),
            ("[5] DESTROYER   — 2 cells", ShipType.DESTROYER),
        ]
        placed = {s[1] for _, s in self.engine.player_grid.ships}
        for i, (label, st) in enumerate(ships_info):
            py = 55 + i * 20
            is_selected = self.engine.state.selected_ship == st
            is_placed = st in placed
            color = self.TEXT_DIM if is_placed else (
                self.ACCENT if is_selected else self.TEXT_COLOR
            )
            flag = " ✓ DEPLOYED" if is_placed else ""
            line = f"{label}{flag}"
            s = self.font_small.render(line, False, color)
            surf.blit(s, (30, py))

        # Direction indicator
        rot = "→ HORIZONTAL" if self.engine.state.placement_horizontal else "↓ VERTICAL"
        rtxt = self.font_small.render(f"[R] {rot}", False, self.TEXT_DIM)
        surf.blit(rtxt, (30, 165))

        # Player grid (left)
        gs = self.CELL_SIZE
        ox = 30
        oy = 195
        self._draw_grid(surf, self.engine.player_grid, ox, oy, show_ships=True)

        # Enemy grid (right, just outline)
        ex = self.BASE_WIDTH // 2 + 30
        ey = 195
        self._draw_grid(surf, self.engine.enemy_grid, ex, ey, show_ships=False)

        # Enemy label
        elbl = self.font_small.render("ENEMY WATERS (HIDDEN)", False, self.TEXT_DIM)
        surf.blit(elbl, (ex, ey - 22))

        # Status bar
        msg = self.engine.state.message or "Select a ship and press ENTER to deploy"
        mc = self.ACCENT if self.engine.state.message else self.TEXT_DIM
        m = self.font_small.render(msg, False, mc)
        surf.blit(m, (30, 580))

        # F11 hint
        f11 = self.font_tiny.render("[F11] FULLSCREEN", False, self.TEXT_DIM)
        surf.blit(f11, (self.BASE_WIDTH - 130, 580))

    def _draw_battle_phase(self, surf: pygame.Surface) -> None:
        phase = self.engine.state.phase
        is_player = phase == Phase.PLAYER_TURN

        # Phase indicator
        label = "◈ YOUR TURN ◈" if is_player else "◈ ENEMY TURN ◈"
        color = self.ACCENT if is_player else self.HIT_COLOR
        pulse = 0.7 + 0.3 * math.sin(self._anim_time * 4)
        r_color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))
        h = self.font_medium.render(label, False, r_color)
        r = h.get_rect(center=(self.BASE_WIDTH // 2, 22))
        surf.blit(h, r)

        gs = self.CELL_SIZE

        # Left: Player grid
        pl_ox = 30
        pl_oy = 45
        self._draw_grid(surf, self.engine.player_grid, pl_ox, pl_oy, show_ships=True)
        pl_lbl = self.font_small.render("YOUR FLEET", False, self.TEXT_DIM)
        surf.blit(pl_lbl, (pl_ox, pl_oy - 20))

        # Right: Enemy grid
        en_ox = self.BASE_WIDTH // 2 + 20
        en_oy = 45
        self._draw_grid(surf, self.engine.enemy_grid, en_ox, en_oy, show_ships=False)
        en_lbl = self.font_small.render("ENEMY WATERS", False, self.TEXT_DIM)
        surf.blit(en_lbl, (en_ox, en_oy - 20))

        # Column headers for enemy grid
        for c in range(self.engine.GRID_SIZE):
            lbl = chr(ord("A") + c)
            s = self.font_tiny.render(lbl, False, self.TEXT_DIM)
            surf.blit(s, (en_ox + c * gs + gs // 2 - s.get_width() // 2, en_oy - 16))

        # Targeting cursor on enemy grid during player turn
        if is_player:
            self._draw_cursor(surf, self._cursor_col, self._cursor_row, gs, en_ox, en_oy, True)
        self._draw_fire_effect(surf)

        # Stats bar
        p_ships = len([s for s in self.engine.player_grid.ships
                      if s[0].hits < s[0].size])
        e_ships = len([s for s in self.engine.enemy_grid.ships
                      if s[0].hits < s[0].size])
        stats = f"YOUR SHIPS: {p_ships}/5    ENEMY SHIPS: {e_ships}/5"
        st = self.font_small.render(stats, False, self.TEXT_COLOR)
        surf.blit(st, (30, 420))

        # Targeting readout
        coord = f"TARGET: {chr(65 + self._cursor_col)}{self._cursor_row + 1}"
        ct = self.font_small.render(coord, False, self.ACCENT)
        surf.blit(ct, (30, 448))

        # Controls hint
        hint = "A-J: COL    1-0: ROW    ENTER: FIRE    ESC: MENU"
        ht = self.font_tiny.render(hint, False, self.TEXT_DIM)
        surf.blit(ht, (30, 480))

        # Legend
        items = [("SHIP", self.SHIP_COLOR), ("HIT", self.HIT_COLOR),
                 ("MISS", self.MISS_COLOR), ("SUNK", self.SUNK_COLOR)]
        lx = 30
        for lbl, col in items:
            pygame.draw.rect(surf, col, (lx, 508, 12, 12))
            t = self.font_tiny.render(lbl, False, self.TEXT_DIM)
            surf.blit(t, (lx + 18, 508))
            lx += 80

        # Message
        msg = self.engine.state.message or ""
        if msg:
            mc = self.HIT_COLOR if "Hit" in msg or "sunk" in msg else self.TEXT_COLOR
            m = self.font_medium.render(msg, False, mc)
            r = m.get_rect(center=(self.BASE_WIDTH // 2, 545))
            surf.blit(m, r)

        # F11
        f11 = self.font_tiny.render("[F11] FULLSCREEN", False, self.TEXT_DIM)
        surf.blit(f11, (self.BASE_WIDTH - 130, 580))

    def _draw_game_over_screen(self, surf: pygame.Surface) -> None:
        # Darken background
        overlay = pygame.Surface((self.BASE_WIDTH, self.BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surf.blit(overlay, (0, 0))

        outcome = self.engine.state.outcome
        if outcome and outcome.value == 1:  # PLAYER_WINS
            main = "■ VICTORY ■"
            color = self.ACCENT
            sub = "The enemy fleet has been destroyed."
        else:
            main = "✕ DEFEAT ✕"
            color = self.HIT_COLOR
            sub = "Your fleet has been destroyed."

        pulse = 0.8 + 0.2 * math.sin(self._anim_time * 3)
        r_color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))
        big = self.font_large.render(main, False, r_color)
        r = big.get_rect(center=(self.BASE_WIDTH // 2, 280))
        surf.blit(big, r)

        s = self.font_medium.render(sub, False, self.TEXT_COLOR)
        r = s.get_rect(center=(self.BASE_WIDTH // 2, 340))
        surf.blit(s, r)

        if (pygame.time.get_ticks() // 600) % 2 == 0:
            p = self.font_small.render("PRESS ENTER TO CONTINUE", False, self.TEXT_DIM)
            r = p.get_rect(center=(self.BASE_WIDTH // 2, 420))
            surf.blit(p, r)

    def draw(self) -> None:
        self._anim_time += 1 / 60
        target = self._fs_surface if self._fullscreen else self._screen
        target.fill(self.BG_COLOR)

        phase = self.engine.state.phase
        if phase == Phase.TITLE:
            self._draw_title_screen(target)
        elif phase == Phase.PLACEMENT:
            self._draw_placement_phase(target)
        elif phase in (Phase.PLAYER_TURN, Phase.ENEMY_TURN):
            self._draw_battle_phase(target)
        elif phase == Phase.GAME_OVER:
            self._draw_battle_phase(target)
            self._draw_game_over_screen(target)

        self._draw_scanlines(target)
        self._draw_vignette(target)
        self._draw_phosphor_glow(target)

        if self._fullscreen and self._fs_surface:
            # Scale to fullscreen
            scaled = pygame.transform.smoothscale(
                target, (self._fs_surface.get_width(), self._fs_surface.get_height())
            )
            self._fs_surface.blit(scaled, (0, 0))
            pygame.display.flip()
        else:
            pygame.display.flip()
        self._clock.tick(60)
