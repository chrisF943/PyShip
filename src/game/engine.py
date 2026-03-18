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

        self._last_col: Optional[int] = None
        self._last_row: int = 0
        self._fire_animation: Optional[tuple[int, int, float]] = None  # col, row, timer
        self.sfx: Optional[object] = None  # Set by main.py

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

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            # Handled in main.py renderer
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state.phase = Phase.TITLE
                return

            if self.state.phase == Phase.TITLE:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state.reset()
                    self.player_grid.clear()
                    self._random_ai_place()
                return

            if self.state.phase == Phase.GAME_OVER:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state.phase = Phase.TITLE
                return

            if self.state.phase == Phase.PLACEMENT:
                if event.key == pygame.K_r:
                    self.state.placement_horizontal = not self.state.placement_horizontal
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    ships = list(ShipType)
                    idx = event.key - pygame.K_1
                    if idx < len(ships):
                        self.state.selected_ship = ships[idx]
                if event.key == pygame.K_RETURN and self.state.selected_ship:
                    self._confirm_placement()
                return

            if self.state.phase == Phase.PLAYER_TURN:
                if event.key in (
                    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                    pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8,
                    pygame.K_9, pygame.K_0
                ):
                    row = event.key - pygame.K_1
                    if event.key == pygame.K_0:
                        row = 9
                    self._last_row = row
                elif event.key in (
                    pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d, pygame.K_e,
                    pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_i, pygame.K_j
                ):
                    col = event.key - pygame.K_a
                    if 0 <= col < self.GRID_SIZE:
                        self._player_fire(col, self._last_row)
                        self._fire_animation = (col, self._last_row, 0.5)

    def _confirm_placement(self) -> None:
        if not self.state.selected_ship:
            return
        ship = Ship(self.state.selected_ship)
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if self.player_grid.can_place(ship, x, y, self.state.placement_horizontal):
                    try:
                        self.player_grid.place_ship(
                            ship, x, y, self.state.placement_horizontal
                        )
                        self.state.selected_ship = None
                        if self.sfx:
                            self.sfx.play("fire")
                        if self.player_grid.all_ships_placed():
                            self.state.phase = Phase.PLAYER_TURN
                            self.state.message = "Your turn — fire at the enemy!"
                        return
                    except PlacementError:
                        pass

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
        self._fire_animation = (col, row, 0.5)
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
            col, row, timer = self._fire_animation
            self._fire_animation = (col, row, timer - 1/60)
            if self._fire_animation[2] <= 0:
                self._fire_animation = None
