"""Core game engine."""

import random
from typing import Optional

import pygame

from src.game.state import (
    CellState,
    GameState,
    Outcome,
    Phase,
    ShipType,
)
from src.board.grid import Grid, PlacementError, Ship


class Engine:
    GRID_SIZE = 10

    def __init__(self) -> None:
        self.state = GameState()
        self.player_grid = Grid(self.GRID_SIZE)
        self.enemy_grid = Grid(self.GRID_SIZE)
        self.player_shots: set[tuple[int, int]] = set()
        self.ai_shot_history: list[tuple[int, int]] = []
        self.ai_last_hit: Optional[tuple[int, int]] = None
        self.ai_pending_hits: list[tuple[int, int]] = []


        self._fire_animation: Optional[tuple[int, int, float, bool]] = None  # col, row, timer, is_enemy_target
        self.sfx: Optional[object] = None  # Set by main.py

        # Shared cursor for placement & targeting
        self.cursor_col = 0
        self.cursor_row = 0

        self._random_ai_place()

    def _random_ai_place(self) -> None:
        for ship_type in ShipType:
            placed = False
            while not placed:
                x = random.randint(0, self.GRID_SIZE - 1)
                y = random.randint(0, self.GRID_SIZE - 1)
                horizontal = random.choice([True, False])
                try:
                    self.enemy_grid.place_ship(Ship(ship_type), x, y, horizontal)
                    placed = True
                except PlacementError:
                    pass

    def _move_cursor(self, event_key: int) -> None:
        """Handle arrow key and A-J / 1-0 cursor movement."""
        if event_key == pygame.K_UP:
            self.cursor_row = max(0, self.cursor_row - 1)
        elif event_key == pygame.K_DOWN:
            self.cursor_row = min(self.GRID_SIZE - 1, self.cursor_row + 1)
        elif event_key == pygame.K_LEFT:
            self.cursor_col = max(0, self.cursor_col - 1)
        elif event_key == pygame.K_RIGHT:
            self.cursor_col = min(self.GRID_SIZE - 1, self.cursor_col + 1)
        elif event_key in (
            pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d, pygame.K_e,
            pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_i, pygame.K_j
        ):
            self.cursor_col = event_key - pygame.K_a
        elif event_key in (
            pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
            pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8,
            pygame.K_9, pygame.K_0
        ):
            if event_key == pygame.K_0:
                self.cursor_row = 9
            else:
                self.cursor_row = event_key - pygame.K_1

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state.phase = Phase.TITLE
                return

            if self.state.phase == Phase.TITLE:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state.reset()
                    self.player_grid.clear()
                    self.enemy_grid.clear()
                    self.player_shots.clear()
                    self.ai_shot_history.clear()
                    self.ai_pending_hits.clear()
                    self.ai_last_hit = None
                    self.cursor_col = 0
                    self.cursor_row = 0
                    self._random_ai_place()
                return

            if self.state.phase == Phase.GAME_OVER:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state.phase = Phase.TITLE
                return

            if self.state.phase == Phase.PLACEMENT:
                # Ship selection (1-5 selects ship type)
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    ships = list(ShipType)
                    idx = event.key - pygame.K_1
                    if idx < len(ships):
                        st = ships[idx]
                        remaining = self._remaining_placements(st)
                        if remaining <= 0:
                            self.state.message = f"{st.name} fully deployed!"
                        else:
                            self.state.selected_ship = st
                            self.state.message = ""
                # Rotation
                elif event.key == pygame.K_r:
                    self.state.placement_horizontal = not self.state.placement_horizontal
                # Place ship at cursor
                elif event.key == pygame.K_RETURN and self.state.selected_ship:
                    self._confirm_placement()
                # Cursor movement (arrows + A-J for col, 6-0 for row)
                elif event.key in (
                    pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
                    pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d, pygame.K_e,
                    pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_i, pygame.K_j,
                    pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0
                ):
                    self._move_cursor(event.key)
                return

            if self.state.phase == Phase.PLAYER_TURN:
                # Cursor movement
                self._move_cursor(event.key)
                # Fire on Enter
                if event.key == pygame.K_RETURN:
                    col, row = self.cursor_col, self.cursor_row
                    if (col, row) in self.player_shots:
                        self.state.message = "Already fired there!"
                    else:
                        self._player_fire(col, row)
                        self._fire_animation = (col, row, 0.5, True)

    def _remaining_placements(self, ship_type: ShipType) -> int:
        placed = sum(1 for s, _, _, _ in self.player_grid.ships if s.type == ship_type)
        return Ship._max_placements(ship_type) - placed

    def _all_ships_placed(self) -> bool:
        for st in ShipType:
            if self._remaining_placements(st) > 0:
                return False
        return True

    def _confirm_placement(self) -> None:
        if not self.state.selected_ship:
            return
        ship = Ship(self.state.selected_ship)
        x, y = self.cursor_col, self.cursor_row
        if self.player_grid.can_place(ship, x, y, self.state.placement_horizontal):
            self.player_grid.place_ship(ship, x, y, self.state.placement_horizontal)
            self.state.message = f"{self.state.selected_ship.name} deployed!"
            if self.sfx:
                self.sfx.play("fire")
            if self._all_ships_placed():
                self.state.selected_ship = None
                self.state.phase = Phase.PLAYER_TURN
                self.state.message = "All ships deployed! Your turn — fire at the enemy!"
                self.cursor_col = 0
                self.cursor_row = 0
            elif self._remaining_placements(self.state.selected_ship) <= 0:
                self.state.selected_ship = None
        else:
            self.state.message = "Can't place there! Try another position."

    def _player_fire(self, col: int, row: int) -> None:
        if (col, row) in self.player_shots:
            return
        self.player_shots.add((col, row))
        result = self.enemy_grid.receive_shot(col, row)
        if self.sfx:
            self.sfx.play("fire")
        if result.hit:
            self.state.message = "Hit!"
            if result.sunk:
                self.state.message = f"You sunk the {result.sunk.name.lower()}!"
                if self.sfx:
                    self.sfx.play("sunk")
            if self.enemy_grid.all_sunk():
                self.state.phase = Phase.GAME_OVER
                self.state.outcome = Outcome.PLAYER_WINS
                self.state.message = "Victory!"
                if self.sfx:
                    self.sfx.play("victory")
                return
        else:
            self.state.message = "Miss."
            if self.sfx:
                self.sfx.play("miss")
        self.state.phase = Phase.ENEMY_TURN

    def _ai_fire(self) -> None:
        if self.ai_pending_hits:
            col, row = self.ai_pending_hits.pop()
        else:
            col = random.randint(0, self.GRID_SIZE - 1)
            row = random.randint(0, self.GRID_SIZE - 1)
            while (col, row) in self.ai_shot_history:
                col = random.randint(0, self.GRID_SIZE - 1)
                row = random.randint(0, self.GRID_SIZE - 1)

        self.ai_shot_history.append((col, row))
        result = self.player_grid.receive_shot(col, row)
        self._fire_animation = (col, row, 0.5, False)
        if self.sfx:
            self.sfx.play("fire")
        if result.hit:
            if result.sunk:
                self.state.message = f"Enemy sunk your {result.sunk.name.lower()}!"
                if self.sfx:
                    self.sfx.play("sunk")
                self.ai_pending_hits = [
                    h for h in self.ai_pending_hits
                    if self.player_grid.get_cell(h[0], h[1]) != CellState.SUNK
                ]
            else:
                self.state.message = "Enemy hit!"
                for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nc, nr = col + dc, row + dr
                    if (0 <= nc < self.GRID_SIZE and 0 <= nr < self.GRID_SIZE and
                            (nc, nr) not in self.ai_shot_history):
                        self.ai_pending_hits.append((nc, nr))
                self.ai_last_hit = (col, row)
            if self.player_grid.all_sunk():
                self.state.phase = Phase.GAME_OVER
                self.state.outcome = Outcome.ENEMY_WINS
                self.state.message = "Defeat!"
                if self.sfx:
                    self.sfx.play("defeat")
                return
        else:
            self.state.message = "Enemy missed."
        self.state.phase = Phase.PLAYER_TURN

    def update(self) -> None:
        if self.state.phase == Phase.ENEMY_TURN:
            self._ai_fire()
        if self._fire_animation:
            col, row, timer, is_enemy = self._fire_animation
            self._fire_animation = (col, row, timer - 1/60, is_enemy)
            if self._fire_animation[2] <= 0:
                self._fire_animation = None
