"""Retro-styled UI renderer."""

import math
import pygame

from src.game.engine import Engine
from src.game.state import CellState, Phase, ShipType


# -------------------------------------------------------------------
# Layout constants — all positions derived from these
# -------------------------------------------------------------------
BASE_WIDTH = 960
BASE_HEIGHT = 720
CELL_SIZE = 32          # Grid cell in pixels
GRID_W = CELL_SIZE * 10  # 320px per grid
GRID_H = CELL_SIZE * 10

# Grid origins
PL_OX = 30             # Player grid left
PL_OY = 80             # Player grid top (below labels)
EN_OX = BASE_WIDTH // 2 + 20  # Enemy grid left
EN_OY = 60             # Enemy grid top (column headers need room above)


class Renderer:
    # Retro palette — tuned for readability
    BG_COLOR = (18, 18, 32)
    GRID_BG = (20, 28, 20)
    GRID_LINE = (60, 90, 60)
    GRID_LINE_BRIGHT = (100, 160, 100)
    SHIP_COLOR = (100, 140, 100)
    SHIP_BRIGHT = (140, 190, 140)
    HIT_COLOR = (255, 70, 40)
    HIT_BRIGHT = (255, 140, 100)
    MISS_COLOR = (70, 100, 140)
    SUNK_COLOR = (180, 50, 40)
    TEXT_COLOR = (200, 230, 180)
    TEXT_DIM = (140, 170, 130)
    ACCENT = (255, 220, 80)

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._fullscreen = False
        self._init_fonts()

        # The game always renders to this fixed-size surface
        self._game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))

        # Windowed mode display
        self._screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("PyShip — Battleship")
        self._clock = pygame.time.Clock()
        self._anim_time = 0.0

        # Scaling state for fullscreen
        self._scale = 1.0
        self._offset_x = 0
        self._offset_y = 0

        # Targeting cursor
        self._cursor_col = 0
        self._cursor_row = 0

        # Procedural ship sprites
        self._ship_sprites = self._generate_ship_sprites()

    def _generate_ship_sprites(self) -> dict:
        sprites = {}
        for ship_type in ShipType:
            size = {
                ShipType.CARRIER: 5, ShipType.BATTLESHIP: 4,
                ShipType.CRUISER: 3, ShipType.SUBMARINE: 3, ShipType.DESTROYER: 2,
            }[ship_type]
            cell = CELL_SIZE
            surf = pygame.Surface((size * cell, cell), pygame.SRCALPHA)
            for i in range(size):
                x = i * cell
                pygame.draw.rect(surf, self.SHIP_COLOR, (x + 2, 4, cell - 4, cell - 8))
                pygame.draw.rect(surf, self.SHIP_BRIGHT, (x + 4, 4, cell - 8, 3))
            sprites[(ship_type, True)] = surf
        return sprites

    def _init_fonts(self) -> None:
        pygame.font.init()
        self.font_large = pygame.font.SysFont("Menlo", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Menlo", 20, bold=True)
        self.font_small = pygame.font.SysFont("Menlo", 14, bold=False)
        self.font_tiny = pygame.font.SysFont("Menlo", 11, bold=False)

    def _update_scale(self) -> None:
        """Recalculate scale factor and centering offset from current screen size."""
        real_w, real_h = self._screen.get_size()
        scale_x = real_w / BASE_WIDTH
        scale_y = real_h / BASE_HEIGHT
        self._scale = min(scale_x, scale_y)
        scaled_w = int(BASE_WIDTH * self._scale)
        scaled_h = int(BASE_HEIGHT * self._scale)
        self._offset_x = (real_w - scaled_w) // 2
        self._offset_y = (real_h - scaled_h) // 2

    def _toggle_fullscreen(self) -> None:
        if not self._fullscreen:
            self._screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self._fullscreen = True
        else:
            self._screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
            self._fullscreen = False
        self._update_scale()

    def handle_resize(self) -> None:
        """Call when a VIDEORESIZE event is received."""
        if not self._fullscreen:
            self._update_scale()

    def _blit_text(self, surf: pygame.Surface, text: str, x: int, y: int,
                   color: tuple[int, int, int]) -> None:
        s = self.font_small.render(text, False, color)
        surf.blit(s, (x, y))

    # -------------------------------------------------------------------
    # Cell / grid drawing
    # -------------------------------------------------------------------
    def _draw_cell(self, surf: pygame.Surface, col: int, row: int,
                   cell: CellState, gs: int, ox: int, oy: int,
                   show_ship: bool = False) -> None:
        x = ox + col * gs + 2
        y = oy + row * gs + 2
        w, h = gs - 4, gs - 4

        if cell == CellState.SHIP and show_ship:
            pygame.draw.rect(surf, (20, 40, 70), (x, y, w, h))
            pygame.draw.rect(surf, self.SHIP_COLOR, (x, y, w, h))
            pygame.draw.rect(surf, self.SHIP_BRIGHT, (x + 2, y + 2, w - 4, 3))
        elif cell == CellState.EMPTY:
            pygame.draw.rect(surf, (18, 35, 65), (x, y, w, h))
        elif cell == CellState.HIT:
            pygame.draw.rect(surf, (20, 40, 70), (x, y, w, h))
            self._draw_hit(surf, x, y, w, h)
        elif cell == CellState.MISS:
            pygame.draw.rect(surf, (18, 35, 65), (x, y, w, h))
            self._draw_miss(surf, x, y, w, h)
        elif cell == CellState.SUNK:
            pygame.draw.rect(surf, (30, 10, 10), (x, y, w, h))
            self._draw_hit(surf, x, y, w, h)

    def _draw_hit(self, surf: pygame.Surface, x: int, y: int, w: int, h: int) -> None:
        intensity = 0.7 + 0.3 * math.sin(self._anim_time * 6)
        c = (int(255 * intensity), int(70 * intensity), int(40 * intensity))
        cx, cy = x + w // 2, y + h // 2
        t = max(2, w // 5)
        pygame.draw.line(surf, c, (x + 4, y + 4), (x + w - 4, y + h - 4), t)
        pygame.draw.line(surf, c, (x + w - 4, y + 4), (x + 4, y + h - 4), t)

    def _draw_miss(self, surf: pygame.Surface, x: int, y: int, w: int, h: int) -> None:
        cx, cy = x + w // 2, y + h // 2
        r = w // 4
        pygame.draw.circle(surf, self.MISS_COLOR, (cx, cy), r, 2)
        pygame.draw.circle(surf, (70, 90, 120), (cx, cy), 2)

    def _draw_grid(self, surf: pygame.Surface, grid, ox: int, oy: int,
                   show_ships: bool = False, title: str = "") -> None:
        gs = CELL_SIZE
        sz = grid.size

        if title:
            t = self.font_small.render(title, False, self.TEXT_DIM)
            surf.blit(t, (ox, oy - 22))

        # Column labels (A-J)
        for c in range(sz):
            lbl = chr(ord("A") + c)
            s = self.font_tiny.render(lbl, False, self.TEXT_DIM)
            surf.blit(s, (ox + c * gs + gs // 2 - s.get_width() // 2, oy - 16))

        # Row labels (1-10)
        for r in range(sz):
            lbl = str(r + 1)
            s = self.font_tiny.render(lbl, False, self.TEXT_DIM)
            surf.blit(s, (ox - 18, oy + r * gs + gs // 2 - s.get_height() // 2))

        # Grid background
        bg = pygame.Surface((sz * gs, sz * gs), pygame.SRCALPHA)
        bg.fill((12, 18, 12, 230))
        surf.blit(bg, (ox, oy))

        # Border
        pygame.draw.rect(surf, self.GRID_LINE_BRIGHT,
                        (ox - 1, oy - 1, sz * gs + 2, sz * gs + 2), 1)

        # Grid lines
        for i in range(1, sz):
            pygame.draw.line(surf, self.GRID_LINE,
                           (ox + i * gs, oy), (ox + i * gs, oy + sz * gs))
            pygame.draw.line(surf, self.GRID_LINE,
                           (ox, oy + i * gs), (ox + sz * gs, oy + i * gs))

        # Cells
        for row in range(sz):
            for col in range(sz):
                self._draw_cell(surf, col, row, grid.cells[row][col],
                               gs, ox, oy, show_ships)

    def _draw_cursor(self, surf: pygame.Surface, col: int, row: int,
                     gs: int, ox: int, oy: int) -> None:
        pulse = 0.5 + 0.5 * math.sin(self._anim_time * 8)
        alpha = int(60 + 60 * pulse)
        x, y = ox + col * gs, oy + row * gs
        rect = pygame.Surface((gs, gs), pygame.SRCALPHA)
        rect.fill((220, 200, 70, alpha))
        surf.blit(rect, (x, y))

    def _draw_fire_effect(self, surf: pygame.Surface) -> None:
        if not self.engine._fire_animation:
            return
        col, row, timer = self.engine._fire_animation
        gs = CELL_SIZE
        x = EN_OX + col * gs + gs // 2
        y = EN_OY + row * gs + gs // 2
        radius = int((0.5 - timer) * gs * 2)
        if radius > 0:
            alpha = int(timer * 2 * 200)
            ring = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 150, 50, alpha), (radius + 2, radius + 2), radius, 2)
            surf.blit(ring, (x - radius - 2, y - radius - 2))

    # -------------------------------------------------------------------
    # Screen overlays
    # -------------------------------------------------------------------
    def _draw_scanlines(self, surf: pygame.Surface) -> None:
        for y in range(0, BASE_HEIGHT, 4):
            pygame.draw.line(surf, (0, 0, 0, 15), (0, y), (BASE_WIDTH, y))

    def _draw_vignette(self, surf: pygame.Surface) -> None:
        for i in range(50):
            alpha = int(40 * (i / 50) ** 1.2)
            pygame.draw.rect(surf, (0, 0, 0, alpha),
                           (i, i, BASE_WIDTH - 2 * i, BASE_HEIGHT - 2 * i), 1)

    # -------------------------------------------------------------------
    # Phase screens
    # -------------------------------------------------------------------
    def _draw_title_screen(self, surf: pygame.Surface) -> None:
        surf.fill(self.BG_COLOR)

        # Wordmark
        title = self.font_large.render("PyShip", False, self.ACCENT)
        r = title.get_rect(center=(BASE_WIDTH // 2, 150))
        surf.blit(title, r)

        # Subtitle
        sub = self.font_medium.render("BATTLESHIP", False, self.TEXT_COLOR)
        r = sub.get_rect(center=(BASE_WIDTH // 2, 205))
        surf.blit(sub, r)

        # Divider
        div = pygame.Surface((300, 2), pygame.SRCALPHA)
        div.fill((100, 160, 100, 150))
        surf.blit(div, (BASE_WIDTH // 2 - 150, 225))

        # Blinking prompt
        if (pygame.time.get_ticks() // 600) % 2 == 0:
            p = self.font_medium.render("PRESS ENTER TO DEPLOY", False, self.ACCENT)
            r = p.get_rect(center=(BASE_WIDTH // 2, 310))
            surf.blit(p, r)

        # Tagline — larger font for readability
        c = self.font_medium.render("A Retro Battleship Experience", False, self.TEXT_COLOR)
        r = c.get_rect(center=(BASE_WIDTH // 2, 355))
        surf.blit(c, r)

        # Controls panel
        controls = [
            ("CONTROLS", True),
            ("A-J  :  Column (A=1, J=10)", False),
            ("1-0  :  Row    (0 = 10)", False),
            ("Enter:  Fire", False),
            ("R    :  Rotate ship", False),
            ("F11  :  Fullscreen", False),
            ("Esc  :  Back to title", False),
        ]
        cy = 430
        for text, is_header in controls:
            color = self.TEXT_COLOR if is_header else self.TEXT_COLOR
            f = self.font_medium if is_header else self.font_medium
            s = f.render(text, False, color)
            r = s.get_rect(center=(BASE_WIDTH // 2, cy))
            surf.blit(s, r)
            cy += 32 if is_header else 28

    def _draw_placement_phase(self, surf: pygame.Surface) -> None:
        surf.fill(self.BG_COLOR)

        # Header
        h = self.font_medium.render("DEPLOY YOUR FLEET", False, self.ACCENT)
        r = h.get_rect(center=(BASE_WIDTH // 2, 28))
        surf.blit(h, r)

        # Ship selection list (left side)
        ships_info = [
            ("[1]  CARRIER     5 cells", ShipType.CARRIER),
            ("[2]  BATTLESHIP 4 cells", ShipType.BATTLESHIP),
            ("[3]  CRUISER     3 cells", ShipType.CRUISER),
            ("[4]  SUBMARINE   3 cells", ShipType.SUBMARINE),
            ("[5]  DESTROYER   2 cells", ShipType.DESTROYER),
        ]
        placed = {s[1] for _, s in self.engine.player_grid.ships}
        for i, (label, st) in enumerate(ships_info):
            py = 60 + i * 24
            is_selected = self.engine.state.selected_ship == st
            is_placed = st in placed
            if is_placed:
                color = self.TEXT_DIM
                flag = "  [DEPLOYED]"
            elif is_selected:
                color = self.ACCENT
                flag = "  [SELECTED]"
            else:
                color = self.TEXT_COLOR
                flag = ""
            line = label + flag
            s = self.font_small.render(line, False, color)
            surf.blit(s, (30, py))

        # Direction indicator
        rot = "HORIZONTAL [R]" if self.engine.state.placement_horizontal else "VERTICAL [R]"
        rtxt = self.font_small.render(rot, False, self.TEXT_DIM)
        surf.blit(rtxt, (30, 195))

        # Player grid (left, below ship list)
        pl_oy = 225
        pl_lbl = self.font_small.render("YOUR FLEET", False, self.TEXT_DIM)
        surf.blit(pl_lbl, (PL_OX, pl_oy - 20))
        self._draw_grid(surf, self.engine.player_grid, PL_OX, pl_oy, show_ships=True)

        # Enemy grid (right, hidden)
        en_oy = 225
        en_lbl = self.font_small.render("ENEMY WATERS (HIDDEN)", False, self.TEXT_DIM)
        surf.blit(en_lbl, (EN_OX, en_oy - 20))
        self._draw_grid(surf, self.engine.enemy_grid, EN_OX, en_oy, show_ships=False)

        # Message
        msg = self.engine.state.message or "Select a ship, press Enter to deploy"
        mc = self.ACCENT if self.engine.state.message else self.TEXT_DIM
        m = self.font_small.render(msg, False, mc)
        surf.blit(m, (30, 650))

        # F11
        f11 = self.font_tiny.render("[F11] Fullscreen", False, self.TEXT_DIM)
        surf.blit(f11, (BASE_WIDTH - 110, 650))

    def _draw_battle_phase(self, surf: pygame.Surface) -> None:
        phase = self.engine.state.phase
        is_player = phase == Phase.PLAYER_TURN

        # Phase indicator
        label = "YOUR TURN" if is_player else "ENEMY TURN"
        color = self.ACCENT if is_player else self.HIT_COLOR
        pulse = 0.7 + 0.3 * math.sin(self._anim_time * 4)
        r_color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))
        h = self.font_medium.render(label, False, r_color)
        r = h.get_rect(center=(BASE_WIDTH // 2, 26))
        surf.blit(h, r)

        gs = CELL_SIZE

        # --- Left: Player grid ---
        pl_lbl = self.font_small.render("YOUR FLEET", False, self.TEXT_DIM)
        surf.blit(pl_lbl, (PL_OX, PL_OY - 20))
        self._draw_grid(surf, self.engine.player_grid, PL_OX, PL_OY, show_ships=True)

        # --- Right: Enemy grid ---
        en_lbl = self.font_small.render("ENEMY WATERS", False, self.TEXT_DIM)
        surf.blit(en_lbl, (EN_OX, EN_OY - 20))
        self._draw_grid(surf, self.engine.enemy_grid, EN_OX, EN_OY, show_ships=False)

        # Targeting cursor on enemy grid
        if is_player:
            self._draw_cursor(surf, self._cursor_col, self._cursor_row, gs, EN_OX, EN_OY)
        self._draw_fire_effect(surf)

        # --- Info panel (right of grids) ---
        panel_x = EN_OX + GRID_W + 20
        panel_y = 60

        # Ship status
        panel_title = self.font_small.render("FLEET STATUS", False, self.TEXT_COLOR)
        surf.blit(panel_title, (panel_x, panel_y))
        panel_y += 22

        for ship, sx, sy, horiz in self.engine.player_grid.ships:
            damage = "■■■■■"[:ship.hits] + "-----"[:ship.size - ship.hits]
            stype = ship.type.name
            color = self.SUNK_COLOR if ship.hits >= ship.size else self.TEXT_DIM
            line = f"  {stype:<12}{damage}"
            s = self.font_tiny.render(line, False, color)
            surf.blit(s, (panel_x, panel_y))
            panel_y += 14

        panel_y += 10

        # Divider
        div = pygame.Surface((panel_x + 120, 1), pygame.SRCALPHA)
        div.fill((80, 120, 80, 100))
        surf.blit(div, (panel_x, panel_y))
        panel_y += 12

        # Targeting coord
        if is_player:
            coord = f"TARGET: {chr(65 + self._cursor_col)}{self._cursor_row + 1}"
        else:
            coord = "TARGETING..."
        ct = self.font_small.render(coord, False, self.ACCENT)
        surf.blit(ct, (panel_x, panel_y))
        panel_y += 30

        # Controls
        for line in ["A-J  : Column", "1-0  : Row", "Enter: Fire", "Esc  : Menu"]:
            s = self.font_tiny.render(line, False, self.TEXT_DIM)
            surf.blit(s, (panel_x, panel_y))
            panel_y += 16

        # Legend (far right)
        lx = panel_x
        ly = 560
        legend_title = self.font_tiny.render("LEGEND", False, self.TEXT_DIM)
        surf.blit(legend_title, (lx, ly))
        ly += 16
        for lbl, col in [
            ("Ship", self.SHIP_COLOR), ("Hit", self.HIT_COLOR),
            ("Miss", self.MISS_COLOR), ("Sunk", self.SUNK_COLOR)
        ]:
            pygame.draw.rect(surf, col, (lx, ly, 10, 10))
            t = self.font_tiny.render(lbl, False, self.TEXT_DIM)
            surf.blit(t, (lx + 16, ly))
            lx += 70
            if lbl == "Miss":
                lx = panel_x
                ly += 18

        # Message bar (below grids, spanning both)
        msg = self.engine.state.message or ""
        if msg:
            mc = self.HIT_COLOR if any(k in msg for k in ("Hit", "hit", "sunk")) else self.TEXT_COLOR
            m = self.font_medium.render(msg, False, mc)
            r = m.get_rect(center=(BASE_WIDTH // 2, 620))
            surf.blit(m, r)

        # F11
        f11 = self.font_tiny.render("[F11] Fullscreen", False, self.TEXT_DIM)
        surf.blit(f11, (BASE_WIDTH - 110, 650))

    def _draw_game_over_screen(self, surf: pygame.Surface) -> None:
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))

        win = self.engine.state.outcome and self.engine.state.outcome.value == 1
        main = "VICTORY" if win else "DEFEAT"
        color = self.ACCENT if win else self.HIT_COLOR

        pulse = 0.8 + 0.2 * math.sin(self._anim_time * 3)
        r_color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))
        big = self.font_large.render(main, False, r_color)
        r = big.get_rect(center=(BASE_WIDTH // 2, 260))
        surf.blit(big, r)

        sub_text = "The enemy fleet has been destroyed." if win else "Your fleet has been destroyed."
        s = self.font_medium.render(sub_text, False, self.TEXT_COLOR)
        r = s.get_rect(center=(BASE_WIDTH // 2, 320))
        surf.blit(s, r)

        if (pygame.time.get_ticks() // 600) % 2 == 0:
            p = self.font_small.render("PRESS ENTER TO CONTINUE", False, self.TEXT_DIM)
            r = p.get_rect(center=(BASE_WIDTH // 2, 400))
            surf.blit(p, r)

    # -------------------------------------------------------------------
    # Main draw loop
    # -------------------------------------------------------------------
    def draw(self) -> None:
        self._anim_time += 1 / 60

        # Always draw to the fixed-size game surface (960×720)
        surf = self._game_surface
        surf.fill(self.BG_COLOR)

        phase = self.engine.state.phase
        if phase == Phase.TITLE:
            self._draw_title_screen(surf)
        elif phase == Phase.PLACEMENT:
            self._draw_placement_phase(surf)
        elif phase in (Phase.PLAYER_TURN, Phase.ENEMY_TURN):
            self._draw_battle_phase(surf)
        elif phase == Phase.GAME_OVER:
            self._draw_battle_phase(surf)
            self._draw_game_over_screen(surf)

        self._draw_scanlines(surf)
        self._draw_vignette(surf)

        # Scale and blit to the actual display
        self._screen.fill((0, 0, 0))
        scaled_w = int(BASE_WIDTH * self._scale)
        scaled_h = int(BASE_HEIGHT * self._scale)
        scaled = pygame.transform.smoothscale(surf, (scaled_w, scaled_h))
        self._screen.blit(scaled, (self._offset_x, self._offset_y))

        pygame.display.flip()
        self._clock.tick(60)
