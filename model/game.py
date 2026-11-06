from enums.game import Action, Outcome, Phase
from model.bot import Bot
from model.hand import Hand
from model.player import Player
from model.shoe import Shoe

MIN_PLAYERS = 1
MAX_PLAYERS = 7
NUM_DECKS = 7
MIN_BET = 1
DEALER_STANDS_ON = 17

PAYOUT_MULTIPLIERS = {
    Outcome.BLACKJACK: 2.5,
    Outcome.WIN: 2,
    Outcome.PUSH: 1,
    Outcome.LOSE: 0,
}


class BlackjackGame:
    """Moteur de la table, indépendant de l'interface.

    L'humain agit via `place_bet`, `deal`, `play` et `new_round`. Tout le reste
    (distribution, bots, croupier) avance d'un pas à chaque appel de `advance`,
    ce qui laisse l'interface libre de rythmer la partie.
    """

    def __init__(self, num_players, shoe=None):
        if not MIN_PLAYERS <= num_players <= MAX_PLAYERS:
            raise ValueError(f"num_players must be in {MIN_PLAYERS}..{MAX_PLAYERS}")

        self.shoe = shoe or Shoe(NUM_DECKS)
        self.dealer = Hand()
        self.human = Player("Vous")

        human_seat = (num_players - 1) // 2
        self.players = [Bot(f"Bot {i + 1}") for i in range(num_players - 1)]
        self.players.insert(human_seat, self.human)

        self.phase = Phase.BETTING
        self.current_index = None
        self.hand_index = 0
        self.hole_hidden = True
        self.just_shuffled = False
        self._deal_queue = []

    # --- État ---

    @property
    def current_player(self):
        return None if self.current_index is None else self.players[self.current_index]

    @property
    def current_hand(self):
        player = self.current_player
        return None if player is None else player.hands[self.hand_index]

    @property
    def awaiting_human(self):
        return self.phase is Phase.PLAYERS and self.current_player is self.human

    @property
    def is_automatic(self):
        """True when `advance` has work to do without waiting for the human."""
        return self.phase in (Phase.DEALING, Phase.PLAYERS, Phase.DEALER) and not self.awaiting_human

    @property
    def is_broke(self):
        return self.phase is Phase.BETTING and self.human.bet == 0 and self.human.funds < MIN_BET

    def visible_dealer_value(self):
        cards = self.dealer.cards
        if not cards:
            return 0
        return cards[0].card_value() if self.hole_hidden else self.dealer.get_value()

    def can_double(self):
        hand = self.current_hand
        return hand is not None and len(hand.cards) == 2 and self.current_player.funds >= hand.bet

    def can_split(self):
        player = self.current_player
        if player is None or len(player.hands) > 1:
            return False
        hand = self.current_hand
        return hand.is_pair() and player.funds >= hand.bet

    def _is_legal(self, action):
        if action is Action.DOUBLE:
            return self.can_double()
        if action is Action.SPLIT:
            return self.can_split()
        return True

    # --- Actions de l'humain ---

    def place_bet(self, amount):
        if self.phase is not Phase.BETTING or amount > self.human.funds:
            return False
        self.human.funds -= amount
        self.human.hands[0].bet += amount
        return True

    def clear_bet(self):
        if self.phase is Phase.BETTING:
            self.human.funds += self.human.bet
            self.human.hands[0].bet = 0

    def deal(self):
        if self.phase is not Phase.BETTING or self.human.bet < MIN_BET:
            return False

        for player in self.players:
            if isinstance(player, Bot):
                bet = player.choose_bet()
                player.hands[0].bet = bet
                player.funds -= bet

        contenders = [player.hands[0] for player in self.players if player.bet > 0]
        self._deal_queue = (contenders + [self.dealer]) * 2
        self.hole_hidden = True
        self.just_shuffled = False
        self.phase = Phase.DEALING
        return True

    def play(self, action):
        """Plays an action for the human. Returns False if it isn't allowed."""
        if not self.awaiting_human or not self._is_legal(action):
            return False
        self._apply(action)
        return True

    def new_round(self):
        if self.phase is not Phase.ROUND_OVER:
            return False
        for player in self.players:
            player.reset_round()
        self.dealer = Hand()
        if self.shoe.needs_shuffle():
            self.shoe.shuffle()
            self.just_shuffled = True
        self.current_index = None
        self.phase = Phase.BETTING
        return True

    # --- Déroulement automatique ---

    def advance(self):
        """Performs one automatic step: one card dealt, or one bot/dealer move."""
        if not self.is_automatic:
            return
        if self.phase is Phase.DEALING:
            self._deal_step()
        elif self.phase is Phase.PLAYERS:
            action = self.current_player.decide(self.current_hand, self.dealer.cards[0])
            self._apply(action if self._is_legal(action) else Action.STAND)
        else:
            self._dealer_step()

    def _deal_step(self):
        self._deal_queue.pop(0).add_card(self.shoe.deal_card())
        if self._deal_queue:
            return
        if self.dealer.is_blackjack():
            self.phase = Phase.DEALER
        else:
            self.phase = Phase.PLAYERS
            self._start_turn(0)

    def _start_turn(self, index):
        """Gives the turn to the first seat from `index` that can still act."""
        for i in range(index, len(self.players)):
            player = self.players[i]
            if player.bet > 0 and player.hands[0].get_value() < 21:
                self.current_index = i
                self.hand_index = 0
                return
        self.current_index = None
        self.hand_index = 0
        self.phase = Phase.DEALER

    def _next_hand(self):
        """Moves to the seat's next playable hand, or to the next seat."""
        hands = self.current_player.hands
        for i in range(self.hand_index + 1, len(hands)):
            if hands[i].get_value() < 21:
                self.hand_index = i
                return
        self._start_turn(self.current_index + 1)

    def _apply(self, action):
        hand = self.current_hand
        if action is Action.HIT:
            hand.add_card(self.shoe.deal_card())
            if hand.get_value() >= 21:
                self._next_hand()
        elif action is Action.DOUBLE:
            self.current_player.funds -= hand.bet
            hand.bet *= 2
            hand.add_card(self.shoe.deal_card())
            self._next_hand()
        elif action is Action.SPLIT:
            self._split()
        else:
            self._next_hand()

    def _split(self):
        player = self.current_player
        first = self.current_hand
        second = Hand(bet=first.bet, from_split=True)
        split_aces = first.cards[0].rank == 'A'

        player.funds -= first.bet
        first.from_split = True
        second.add_card(first.cards.pop())
        player.hands.append(second)
        first.add_card(self.shoe.deal_card())
        second.add_card(self.shoe.deal_card())

        if split_aces:
            self._start_turn(self.current_index + 1)
        elif first.get_value() >= 21:
            self._next_hand()

    def _dealer_step(self):
        if self.hole_hidden:
            self.hole_hidden = False
        elif self._dealer_must_draw():
            self.dealer.add_card(self.shoe.deal_card())
        else:
            self._settle()

    def _dealer_must_draw(self):
        someone_in_play = any(
            hand.bet > 0 and not hand.is_bust() and not hand.is_blackjack()
            for player in self.players for hand in player.hands
        )
        return someone_in_play and self.dealer.get_value() < DEALER_STANDS_ON

    def _settle(self):
        for player in self.players:
            for hand in player.hands:
                if hand.bet > 0:
                    hand.outcome = self._outcome(hand)
                    hand.payout = hand.bet * PAYOUT_MULTIPLIERS[hand.outcome]
                    player.funds += hand.payout
        self.phase = Phase.ROUND_OVER

    def _outcome(self, hand):
        dealer = self.dealer
        if hand.is_bust():
            return Outcome.LOSE
        if hand.is_blackjack():
            return Outcome.PUSH if dealer.is_blackjack() else Outcome.BLACKJACK
        if dealer.is_blackjack():
            return Outcome.LOSE
        if dealer.is_bust() or hand.get_value() > dealer.get_value():
            return Outcome.WIN
        if hand.get_value() == dealer.get_value():
            return Outcome.PUSH
        return Outcome.LOSE
