class Hand:
    def __init__(self, bet=0, from_split=False):
        self.cards = []
        self.bet = bet
        self.from_split = from_split
        self.outcome = None
        self.payout = 0

    def add_card(self, card):
        self.cards.append(card)

    def get_value(self):
        """Returns the best value of the hand, counting aces as 1 when needed."""
        value = sum(card.card_value() for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == 'A')
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def is_blackjack(self):
        """A 21 made after a split is not a blackjack."""
        return len(self.cards) == 2 and self.get_value() == 21 and not self.from_split

    def is_bust(self):
        return self.get_value() > 21

    def is_pair(self):
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank
