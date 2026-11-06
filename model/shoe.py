import random

from model.deck import Deck


class Shoe:
    """Sabot de plusieurs jeux complets, remélangé une fois la carte de coupe atteinte."""

    PENETRATION = 0.75

    def __init__(self, num_decks=7):
        self.num_decks = num_decks
        self.cards = []
        self.shuffle()

    @property
    def size(self):
        return self.num_decks * 52

    def shuffle(self):
        self.cards = [card for _ in range(self.num_decks) for card in Deck().cards]
        random.shuffle(self.cards)

    def deal_card(self):
        return self.cards.pop()

    def needs_shuffle(self):
        return len(self.cards) <= self.size * (1 - self.PENETRATION)
