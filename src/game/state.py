"""Game state and shared types."""

from enum import Enum, auto


class CellState(Enum):
    EMPTY = auto()
    SHIP = auto()
    HIT = auto()
    MISS = auto()
    SUNK = auto()


class ShipType(Enum):
    CARRIER = auto()      # 5 cells
    BATTLESHIP = auto()   # 4 cells
    CRUISER = auto()      # 3 cells
    SUBMARINE = auto()    # 3 cells
    DESTROYER = auto()    # 2 cells


class Phase(Enum):
    TITLE = auto()
    PLACEMENT = auto()
    PLAYER_TURN = auto()
    ENEMY_TURN = auto()
    GAME_OVER = auto()


class Outcome(Enum):
    PLAYER_WINS = auto()
    ENEMY_WINS = auto()


class GameState:
    def __init__(self) -> None:
        self.phase = Phase.TITLE
        self.outcome: Outcome | None = None
        self.selected_ship: ShipType | None = None
        self.placement_horizontal = True
        self.message = ""

    def reset(self) -> None:
        self.phase = Phase.PLACEMENT
        self.outcome = None
        self.selected_ship = None
        self.placement_horizontal = True
        self.message = ""
