"""Board grid and ship management."""

from src.game.state import CellState, ShipType


class PlacementError(Exception):
    pass


class Ship:
    def __init__(self, ship_type: ShipType) -> None:
        self.type = ship_type
        self.size = self._size_for(ship_type)
        self.hits = 0

    @staticmethod
    def _size_for(st: ShipType) -> int:
        sizes = {
            ShipType.CARRIER: 5,
            ShipType.BATTLESHIP: 4,
            ShipType.CRUISER: 3,
            ShipType.SUBMARINE: 3,
            ShipType.DESTROYER: 2,
        }
        return sizes[st]


class Grid:
    def __init__(self, size: int = 10) -> None:
        self.size = size
        self.cells: list[list[CellState]] = [
            [CellState.EMPTY for _ in range(size)] for _ in range(size)
        ]
        self.ships: list[tuple[Ship, int, int, bool]] = []

    def can_place(self, ship: Ship, x: int, y: int, horizontal: bool) -> bool:
        cells = self._ship_cells(x, y, ship.size, horizontal)
        if not all(0 <= c < self.size and 0 <= r < self.size for c, r in cells):
            return False
        return all(self.cells[r][c] == CellState.EMPTY for c, r in cells)

    def place_ship(self, ship: Ship, x: int, y: int, horizontal: bool) -> None:
        if not self.can_place(ship, x, y, horizontal):
            raise PlacementError()
        for c, r in self._ship_cells(x, y, ship.size, horizontal):
            self.cells[r][c] = CellState.SHIP
        self.ships.append((ship, x, y, horizontal))

    def _ship_cells(self, x: int, y: int, size: int, horizontal: bool):
        return [(x + i, y) if horizontal else (x, y + i) for i in range(size)]

    def receive_shot(self, col: int, row: int):
        cell = self.cells[row][col]
        if cell == CellState.SHIP:
            self.cells[row][col] = CellState.HIT
            # Find which ship was hit and check if sunk
            for ship, sx, sy, horiz in self.ships:
                cells = self._ship_cells(sx, sy, ship.size, horiz)
                if (col, row) in cells:
                    ship.hits += 1
                    if ship.hits >= ship.size:
                        for c, r in cells:
                            self.cells[r][c] = CellState.SUNK
                        return ShotResult(hit=True, sunk=ship.type)
                    break
            return ShotResult(hit=True, sunk=None)
        elif cell == CellState.EMPTY:
            self.cells[row][col] = CellState.MISS
            return ShotResult(hit=False, sunk=None)
        return ShotResult(hit=False, sunk=None)

    def get_cell(self, col: int, row: int) -> CellState:
        return self.cells[row][col]

    def all_sunk(self) -> bool:
        return all(
            ship.hits >= ship.size for ship, _, _, _ in self.ships
        )

    def all_ships_placed(self) -> bool:
        return len(self.ships) == 5

    def clear(self) -> None:
        self.cells = [
            [CellState.EMPTY for _ in range(self.size)] for _ in range(self.size)
        ]
        self.ships = []


class ShotResult:
    def __init__(self, hit: bool, sunk: ShipType | None) -> None:
        self.hit = hit
        self.sunk = sunk
