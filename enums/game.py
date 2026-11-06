from enum import Enum, auto


class Phase(Enum):
    BETTING = auto()
    DEALING = auto()
    PLAYERS = auto()
    DEALER = auto()
    ROUND_OVER = auto()


class Action(Enum):
    HIT = auto()
    STAND = auto()
    DOUBLE = auto()
    SPLIT = auto()


class Outcome(Enum):
    BLACKJACK = auto()
    WIN = auto()
    PUSH = auto()
    LOSE = auto()
