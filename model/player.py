from model.hand import Hand


class Player:
    def __init__(self, name, funds=100):
        self.name = name
        self.funds = funds
        self.hands = [Hand()]

    @property
    def bet(self):
        """Total staked this round, across all hands."""
        return sum(hand.bet for hand in self.hands)

    def reset_round(self):
        self.hands = [Hand()]
