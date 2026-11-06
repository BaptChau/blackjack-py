from enums.game import Action
from model.player import Player


class Bot(Player):
    """Joueur automatique. Stratégie provisoire : à implémenter plus tard.

    Le moteur n'appelle que `choose_bet` et `decide` : remplacer ces deux
    méthodes suffit pour donner un vrai comportement aux bots.
    """

    DEFAULT_BET = 5

    def choose_bet(self):
        """Returns the amount to bet this round (0 to sit out)."""
        return self.DEFAULT_BET if self.funds >= self.DEFAULT_BET else 0

    def decide(self, hand, dealer_upcard):
        """Returns the Action to play for `hand`; an illegal action counts as STAND."""
        return Action.STAND
