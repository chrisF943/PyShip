"""Retro-styled UI renderer."""

import math
import pygame

from src.game.engine import Engine
from src.game.state import CellState, Phase, ShipType
from src.board.grid import Ship


# -------------------------------------------------------------------
# Layout constants — all positions derived from these
# -------------------------------------------------------------------
BASE_WIDTH = 1152        # 16:10 aspect ratio — fills Retina display fully
BASE_HEIGHT = 720
CELL_SIZE = 36           # Grid cell in pixels
GRID_W = CELL_SIZE * 10  # 360px per grid
GRID_H = CELL_SIZE * 10
GRID_GAP = 72            # Gap between the two grids

# Grid origins — centered horizontally, clear of 50px vignette
PL_OX = (BASE_WIDTH - 2 * GRID_W - GRID_GAP) // 2   # ~180
PL_OY = 101
EN_OX = PL_OX + GRID_W + GRID_GAP                    # ~540
EN_OY = 101


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
        self.font_medium = pygame.font.SysFont("Menlo", 22, bold=True)
        self.font_small = pygame.font.SysFont("Menlo", 20, bold=False)
        self.font_tiny = pygame.font.SysFont("Menlo", 16, bold=False)

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
        s = self.font_small.render(text, True, color)
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
        elif cell == CellState.EMPTY or (cell == CellState.SHIP and not show_ship):
            pygame.draw.rect(surf, (18, 35, 65), (x, y, w, h))
        elif cell == CellState.HIT:
            pygame.draw.rect(surf, (20, 40, 70), (x, y, w, h))
            self._draw_hit(surf, x, y, w, h)
        elif cell == CellState.MISS:
            pygame.draw.rect(surf, (18, 35, 65), (x, y, w, h))
            self._draw_miss(surf, x, y, w, h)
        elif cell == CellState.SUNK:
            pulse = 0.6 + 0.4 * math.sin(self._anim_time * 4)
            r_val = int(80 * pulse)
            pygame.draw.rect(surf, (r_val, 10, 10), (x, y, w, h))
            self._draw_hit(surf, x, y, w, h)
            # Border to outline the sunk ship
            pygame.draw.rect(surf, (180, 40, 40), (x, y, w, h), 2)

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
            t = self.font_small.render(title, True, self.TEXT_COLOR)
            surf.blit(t, (ox, oy - 38))

        # Column labels (A-J)
        for c in range(sz):
            lbl = chr(ord("A") + c)
            s = self.font_tiny.render(lbl, True, self.TEXT_COLOR)
            surf.blit(s, (ox + c * gs + gs // 2 - s.get_width() // 2, oy - 18))

        # Row labels (1-10)
        for r in range(sz):
            lbl = str(r + 1)
            s = self.font_tiny.render(lbl, True, self.TEXT_COLOR)
            surf.blit(s, (ox - s.get_width() - 10, oy + r * gs + gs // 2 - s.get_height() // 2))

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
        col, row, timer, is_enemy = self.engine._fire_animation
        gs = CELL_SIZE
        x = (EN_OX if is_enemy else PL_OX) + col * gs + gs // 2
        y = (EN_OY if is_enemy else PL_OY) + row * gs + gs // 2
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
        title = self.font_large.render("PyShip", True, self.ACCENT)
        r = title.get_rect(center=(BASE_WIDTH // 2, 150))
        surf.blit(title, r)

        # Subtitle
        sub = self.font_medium.render("BATTLESHIP", True, self.TEXT_COLOR)
        r = sub.get_rect(center=(BASE_WIDTH // 2, 205))
        surf.blit(sub, r)

        # Divider
        div = pygame.Surface((300, 2), pygame.SRCALPHA)
        div.fill((100, 160, 100, 150))
        surf.blit(div, (BASE_WIDTH // 2 - 150, 225))

        # Blinking prompt
        if (pygame.time.get_ticks() // 600) % 2 == 0:
            p = self.font_medium.render("PRESS ENTER TO DEPLOY", True, self.ACCENT)
            r = p.get_rect(center=(BASE_WIDTH // 2, 310))
            surf.blit(p, r)

        # Tagline — larger font for readability
        c = self.font_medium.render("A Retro Battleship Experience", True, self.TEXT_COLOR)
        r = c.get_rect(center=(BASE_WIDTH // 2, 355))
        surf.blit(c, r)

        # Controls panel
        controls = [
            ("CONTROLS", True),
            ("Arrows:  Move cursor", False),
            ("A-J   :  Jump to column", False),
            ("1-0   :  Jump to row", False),
            ("Enter :  Place / Fire", False),
            ("R     :  Rotate ship", False),
            ("F11   :  Fullscreen", False),
            ("Esc   :  Back to title", False),
        ]
        cy = 430
        for text, is_header in controls:
            color = self.TEXT_COLOR if is_header else self.TEXT_COLOR
            f = self.font_medium if is_header else self.font_medium
            s = f.render(text, True, color)
            r = s.get_rect(center=(BASE_WIDTH // 2, cy))
            surf.blit(s, r)
            cy += 32 if is_header else 28

    def _draw_placement_phase(self, surf: pygame.Surface) -> None:
        surf.fill(self.BG_COLOR)

        # Header
        h = self.font_medium.render("DEPLOY YOUR FLEET", True, self.ACCENT)
        r = h.get_rect(center=(BASE_WIDTH // 2, 30))
        surf.blit(h, r)

        # Ship selection list (left side)
        ships_info = [
            ("[1] CARRIER", ShipType.CARRIER),
            ("[2] BATTLESHIP", ShipType.BATTLESHIP),
            ("[3] CRUISER", ShipType.CRUISER),
            ("[4] SUBMARINE", ShipType.SUBMARINE),
            ("[5] DESTROYER", ShipType.DESTROYER),
        ]
        for i, (label, st) in enumerate(ships_info):
            py = 56 + i * 22
            is_selected = self.engine.state.selected_ship == st
            placed_count = sum(1 for s, _, _, _ in self.engine.player_grid.ships if s.type == st)
            max_placements = Ship._max_placements(st)
            remaining = max_placements - placed_count
            if remaining <= 0:
                color = self.TEXT_DIM
                flag = " [DEPLOYED]"
            elif is_selected:
                color = self.ACCENT
                flag = f" ({remaining})"
            else:
                color = self.TEXT_COLOR
                flag = f" ({remaining})"
            line = label + flag
            s = self.font_small.render(line, True, color)
            surf.blit(s, (PL_OX, py))

        # Direction indicator
        rot = "HORIZONTAL [R]" if self.engine.state.placement_horizontal else "VERTICAL [R]"
        rtxt = self.font_small.render(rot, True, self.TEXT_COLOR)
        surf.blit(rtxt, (PL_OX, 170))

        # Player grid (left, below ship list)
        pl_oy = 245
        self._draw_grid(surf, self.engine.player_grid, PL_OX, pl_oy,
                        show_ships=True, title="YOUR FLEET")

        # Placement preview (ghost ship at cursor)
        if self.engine.state.selected_ship:
            preview_ship = Ship(self.engine.state.selected_ship)
            cc, cr = self.engine.cursor_col, self.engine.cursor_row
            can_place = self.engine.player_grid.can_place(
                preview_ship, cc, cr, self.engine.state.placement_horizontal
            )
            preview_color = (60, 200, 60, 80) if can_place else (200, 60, 60, 80)
            gs = CELL_SIZE
            cells = []
            for i in range(preview_ship.size):
                if self.engine.state.placement_horizontal:
                    cells.append((cc + i, cr))
                else:
                    cells.append((cc, cr + i))
            for c, r in cells:
                if 0 <= c < 10 and 0 <= r < 10:
                    px = PL_OX + c * gs + 2
                    py_cell = pl_oy + r * gs + 2
                    ghost = pygame.Surface((gs - 4, gs - 4), pygame.SRCALPHA)
                    ghost.fill(preview_color)
                    surf.blit(ghost, (px, py_cell))

            # Also draw the cursor highlight
            self._draw_cursor(surf, cc, cr, gs, PL_OX, pl_oy)

        # Enemy grid (right, hidden)
        en_oy = 245
        self._draw_grid(surf, self.engine.enemy_grid, EN_OX, en_oy,
                        show_ships=False, title="ENEMY WATERS")

        # Message
        msg = self.engine.state.message or "Select ship (1-5), position with arrows, Enter to place"
        mc = self.ACCENT if self.engine.state.message else self.TEXT_COLOR
        m = self.font_small.render(msg, True, mc)
        r = m.get_rect(center=(BASE_WIDTH // 2, 660))
        surf.blit(m, r)

        # F11
        f11 = self.font_tiny.render("[F11] Fullscreen", True, self.TEXT_COLOR)
        f11_r = f11.get_rect(right=BASE_WIDTH - 60, centery=660)
        surf.blit(f11, f11_r)

    def _draw_battle_phase(self, surf: pygame.Surface) -> None:
        phase = self.engine.state.phase
        is_player = phase == Phase.PLAYER_TURN

        # Phase indicator
        label = "YOUR TURN" if is_player else "ENEMY TURN"
        color = self.ACCENT if is_player else self.HIT_COLOR
        pulse = 0.7 + 0.3 * math.sin(self._anim_time * 4)
        r_color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))
        h = self.font_medium.render(label, True, r_color)
        r = h.get_rect(center=(BASE_WIDTH // 2, 30))
        surf.blit(h, r)

        gs = CELL_SIZE

        # --- Left: Player grid ---
        self._draw_grid(surf, self.engine.player_grid, PL_OX, PL_OY,
                        show_ships=True, title="YOUR FLEET")

        # --- Right: Enemy grid ---
        self._draw_grid(surf, self.engine.enemy_grid, EN_OX, EN_OY,
                        show_ships=False, title="ENEMY WATERS")

        # Targeting cursor on enemy grid
        if is_player:
            self._draw_cursor(surf, self.engine.cursor_col, self.engine.cursor_row, gs, EN_OX, EN_OY)
        self._draw_fire_effect(surf)

        # --- Info panel (below grids) ---
        grid_bottom = PL_OY + GRID_H + 15
        panel_x = PL_OX

        # YOUR fleet status (left side)
        panel_title = self.font_small.render("YOUR SHIPS", True, self.ACCENT)
        surf.blit(panel_title, (panel_x, grid_bottom))

        ship_x = panel_x
        ship_y = grid_bottom + 20
        for ship, sx, sy, horiz in self.engine.player_grid.ships:
            damage = "■" * ship.hits + "□" * (ship.size - ship.hits)
            stype = ship.type.name[:4]
            color = self.SUNK_COLOR if ship.hits >= ship.size else self.TEXT_COLOR
            line = f"{stype} {damage}"
            s = self.font_small.render(line, True, color)
            surf.blit(s, (ship_x, ship_y))
            ship_y += 18

        # ENEMY fleet status (right side)
        enemy_title = self.font_small.render("ENEMY SHIPS", True, self.HIT_COLOR)
        enemy_title_r = enemy_title.get_rect(right=EN_OX + GRID_W, top=grid_bottom)
        surf.blit(enemy_title, enemy_title_r)

        enemy_y = grid_bottom + 20
        for ship, sx, sy, horiz in self.engine.enemy_grid.ships:
            stype = ship.type.name[:4]
            is_sunk = ship.hits >= ship.size
            if is_sunk:
                damage = "X" * ship.size
                color = self.SUNK_COLOR
                status = "SUNK"
            else:
                damage = "?" * ship.size
                color = self.TEXT_COLOR
                status = ""
            line = f"{stype} {damage} {status}"
            s = self.font_small.render(line, True, color)
            s_r = s.get_rect(right=EN_OX + GRID_W, top=enemy_y)
            surf.blit(s, s_r)
            enemy_y += 18

        # Targeting coord (centered)
        if is_player:
            coord = f"TARGET: {chr(65 + self.engine.cursor_col)}{self.engine.cursor_row + 1}"
        else:
            coord = "TARGETING..."
        ct = self.font_medium.render(coord, True, self.ACCENT)
        ct_r = ct.get_rect(center=(BASE_WIDTH // 2, grid_bottom + 4))
        surf.blit(ct, ct_r)

        # Controls (centered, below target)
        ctrl_y = grid_bottom + 65
        for line in ["Arrows/A-J/1-0: Move", "Enter: Fire   Esc: Menu"]:
            s = self.font_small.render(line, True, self.TEXT_COLOR)
            ct_r = s.get_rect(center=(BASE_WIDTH // 2, ctrl_y))
            surf.blit(s, ct_r)
            ctrl_y += 18

        # Message bar (bottom, centered) — extra emphasis for sinks
        msg = self.engine.state.message or ""
        if msg:
            is_sink = "sunk" in msg.lower()
            is_hit = any(k in msg for k in ("Hit", "hit")) or is_sink
            if is_sink:
                mc = (255, 100, 50)
                font = self.font_medium
            elif is_hit:
                mc = self.HIT_COLOR
                font = self.font_medium
            else:
                mc = self.TEXT_COLOR
                font = self.font_medium
            m = font.render(msg, True, mc)
            r = m.get_rect(center=(BASE_WIDTH // 2, 620))
            surf.blit(m, r)

        # F11
        f11 = self.font_tiny.render("[F11] Fullscreen", True, self.TEXT_COLOR)
        f11_r = f11.get_rect(right=BASE_WIDTH - 60, centery=660)
        surf.blit(f11, f11_r)

    def _draw_game_over_screen(self, surf: pygame.Surface) -> None:
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))

        win = self.engine.state.outcome and self.engine.state.outcome.value == 1
        main = "VICTORY" if win else "DEFEAT"
        color = self.ACCENT if win else self.HIT_COLOR

        pulse = 0.8 + 0.2 * math.sin(self._anim_time * 3)
        r_color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))
        big = self.font_large.render(main, True, r_color)
        r = big.get_rect(center=(BASE_WIDTH // 2, 260))
        surf.blit(big, r)

        sub_text = "The enemy fleet has been destroyed." if win else "Your fleet has been destroyed."
        s = self.font_medium.render(sub_text, True, self.TEXT_COLOR)
        r = s.get_rect(center=(BASE_WIDTH // 2, 320))
        surf.blit(s, r)

        player_shots = len(self.engine.player_shots)
        enemy_shots = len(self.engine.ai_shot_history)
        shot_text = f"You won with {player_shots} shots!" if win else f"You lost in {enemy_shots} shots."
        st = self.font_medium.render(shot_text, True, color)
        r2 = st.get_rect(center=(BASE_WIDTH // 2, 360))
        surf.blit(st, r2)

        if (pygame.time.get_ticks() // 600) % 2 == 0:
            p = self.font_small.render("PRESS ENTER TO CONTINUE", True, self.TEXT_DIM)
            r = p.get_rect(center=(BASE_WIDTH // 2, 440))
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
