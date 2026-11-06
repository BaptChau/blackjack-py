import unittest
from collections import Counter

from enums.game import Action, Outcome, Phase
from model.card import Card
from model.bot import Bot
from model.game import BlackjackGame
from model.hand import Hand
from model.shoe import Shoe


class RiggedShoe(Shoe):
    """Sabot dont les prochaines cartes sont connues (rangs dans l'ordre de tirage)."""

    def __init__(self, ranks):
        super().__init__(7)
        self.cards += [Card("Spades", rank) for rank in reversed(ranks)]


def start_round(ranks, bet=10, num_players=1):
    game = BlackjackGame(num_players, shoe=RiggedShoe(ranks))
    game.place_bet(bet)
    game.deal()
    run_until_stopped(game)
    return game


def run_until_stopped(game):
    while game.is_automatic:
        game.advance()


class ShoeTests(unittest.TestCase):
    def test_contains_seven_complete_decks(self):
        shoe = Shoe(7)
        self.assertEqual(len(shoe.cards), 364)
        counts = Counter((card.suit, card.rank) for card in shoe.cards)
        self.assertEqual(len(counts), 52)
        self.assertEqual(set(counts.values()), {7})

    def test_needs_shuffle_at_cut_card(self):
        shoe = Shoe(7)
        self.assertFalse(shoe.needs_shuffle())
        shoe.cards = shoe.cards[:91]
        self.assertTrue(shoe.needs_shuffle())


class HandValueTests(unittest.TestCase):
    def hand(self, *ranks):
        hand = Hand()
        for rank in ranks:
            hand.add_card(Card("Spades", rank))
        return hand

    def test_aces_soften_when_needed(self):
        self.assertEqual(self.hand("A", "K").get_value(), 21)
        self.assertEqual(self.hand("A", "A").get_value(), 12)
        self.assertEqual(self.hand("A", "A", "9").get_value(), 21)
        self.assertEqual(self.hand("A", "K", "5").get_value(), 16)

    def test_three_card_21_is_not_blackjack(self):
        self.assertFalse(self.hand("7", "7", "7").is_blackjack())
        self.assertTrue(self.hand("A", "Q").is_blackjack())


class RoundTests(unittest.TestCase):
    # Ordre de tirage en solo : joueur, croupier, joueur, trou, puis suite.

    def test_table_seats_one_human_and_bots(self):
        game = BlackjackGame(7)
        self.assertEqual(len(game.players), 7)
        self.assertEqual(game.players.count(game.human), 1)
        self.assertIs(game.players[3], game.human)

    def test_rejects_invalid_table_size(self):
        for size in (0, 8):
            with self.assertRaises(ValueError):
                BlackjackGame(size)

    def test_cannot_deal_without_bet(self):
        game = BlackjackGame(1)
        self.assertFalse(game.deal())
        self.assertIs(game.phase, Phase.BETTING)

    def test_cannot_bet_more_than_funds(self):
        game = BlackjackGame(1)
        self.assertFalse(game.place_bet(101))
        self.assertEqual(game.human.funds, 100)

    def test_clear_bet_refunds(self):
        game = BlackjackGame(1)
        game.place_bet(25)
        game.clear_bet()
        self.assertEqual((game.human.funds, game.human.bet), (100, 0))

    def test_blackjack_pays_three_to_two(self):
        game = start_round(["A", "9", "K", "8"])
        self.assertIs(game.human.hands[0].outcome, Outcome.BLACKJACK)
        self.assertEqual(game.human.funds, 115)

    def test_dealer_blackjack_ends_round_immediately(self):
        game = start_round(["9", "A", "9", "K"])
        self.assertIs(game.phase, Phase.ROUND_OVER)
        self.assertIs(game.human.hands[0].outcome, Outcome.LOSE)
        self.assertEqual(game.human.funds, 90)

    def test_both_blackjacks_push(self):
        game = start_round(["A", "A", "K", "K"])
        self.assertIs(game.human.hands[0].outcome, Outcome.PUSH)
        self.assertEqual(game.human.funds, 100)

    def test_bust_loses_without_dealer_drawing(self):
        game = start_round(["K", "5", "Q", "6", "9"])
        game.play(Action.HIT)
        run_until_stopped(game)
        self.assertIs(game.human.hands[0].outcome, Outcome.LOSE)
        self.assertEqual(len(game.dealer.cards), 2)

    def test_dealer_draws_to_17_and_stands(self):
        game = start_round(["K", "5", "Q", "6", "6", "K"])
        game.play(Action.STAND)
        run_until_stopped(game)
        self.assertEqual(game.dealer.get_value(), 17)
        self.assertIs(game.human.hands[0].outcome, Outcome.WIN)
        self.assertEqual(game.human.funds, 110)

    def test_double_doubles_bet_and_draws_one_card(self):
        game = start_round(["6", "K", "5", "7", "K"])
        self.assertTrue(game.can_double())
        game.play(Action.DOUBLE)
        run_until_stopped(game)
        self.assertEqual(len(game.human.hands[0].cards), 3)
        self.assertEqual(game.human.bet, 20)
        self.assertEqual(game.human.funds, 120)

    def test_double_refused_without_funds(self):
        game = start_round(["6", "K", "5", "7"], bet=60)
        self.assertFalse(game.can_double())
        self.assertFalse(game.play(Action.DOUBLE))

    def test_double_refused_after_hit(self):
        game = start_round(["2", "K", "3", "7", "4"])
        game.play(Action.HIT)
        self.assertFalse(game.can_double())

    def test_bots_play_around_human(self):
        # Bot 1, Vous, Bot 2, croupier, puis second tour.
        game = start_round(["9", "K", "8", "10", "9", "Q", "8", "7"], num_players=3)
        self.assertTrue(game.awaiting_human)
        self.assertEqual(game.players[0].bet, 5)
        game.play(Action.STAND)
        run_until_stopped(game)
        self.assertIs(game.phase, Phase.ROUND_OVER)
        self.assertEqual([p.funds for p in game.players], [105, 110, 95])

    def test_broke_bot_sits_out(self):
        game = BlackjackGame(2)
        bot = game.players[1] if game.players[0] is game.human else game.players[0]
        bot.funds = 3
        game.place_bet(10)
        game.deal()
        self.assertEqual(bot.bet, 0)
        run_until_stopped(game)
        self.assertEqual(bot.hands[0].cards, [])
        self.assertEqual(bot.funds, 3)

    def test_new_round_resets_and_shuffles_at_cut_card(self):
        game = start_round(["A", "9", "K", "8"])
        game.shoe.cards = game.shoe.cards[:50]
        game.new_round()
        self.assertIs(game.phase, Phase.BETTING)
        self.assertEqual(game.human.hands[0].cards, [])
        self.assertEqual(len(game.shoe.cards), 364)
        self.assertTrue(game.just_shuffled)

    def test_broke_detection(self):
        game = BlackjackGame(1)
        game.human.funds = 0
        self.assertTrue(game.is_broke)


class SplitTests(unittest.TestCase):
    # Tirage : joueur, croupier, joueur, trou, puis une carte par main séparée.

    def test_split_creates_two_hands_with_their_own_bet(self):
        game = start_round(["8", "6", "8", "K", "3", "10"])
        self.assertTrue(game.can_split())
        self.assertTrue(game.play(Action.SPLIT))
        first, second = game.human.hands
        self.assertEqual((first.bet, second.bet), (10, 10))
        self.assertEqual((first.get_value(), second.get_value()), (11, 18))
        self.assertEqual(game.human.funds, 80)
        self.assertIs(game.current_hand, first)

    def test_different_tens_cannot_split(self):
        game = start_round(["K", "6", "Q", "K"])
        self.assertFalse(game.can_split())
        self.assertFalse(game.play(Action.SPLIT))
        self.assertEqual(len(game.human.hands), 1)

    def test_split_refused_after_hit(self):
        game = start_round(["2", "6", "3", "K", "2"])
        game.play(Action.HIT)
        self.assertFalse(game.can_split())

    def test_split_refused_without_funds(self):
        game = start_round(["8", "6", "8", "K"], bet=60)
        self.assertFalse(game.can_split())

    def test_no_second_split(self):
        game = start_round(["8", "6", "8", "K", "8", "10"])
        game.play(Action.SPLIT)
        self.assertTrue(game.human.hands[0].is_pair())
        self.assertFalse(game.can_split())

    def test_hands_are_played_in_order_and_settled_separately(self):
        # Croupier 6 + K = 16, tire un 2 : 18. Main 1 : 8+3+9 = 20 ; main 2 : 8+10 = 18.
        game = start_round(["8", "6", "8", "K", "3", "10", "9", "2"])
        game.play(Action.SPLIT)
        game.play(Action.HIT)
        self.assertEqual(game.hand_index, 0)
        game.play(Action.STAND)
        self.assertEqual(game.hand_index, 1)
        game.play(Action.STAND)
        run_until_stopped(game)
        first, second = game.human.hands
        self.assertIs(first.outcome, Outcome.WIN)
        self.assertIs(second.outcome, Outcome.PUSH)
        self.assertEqual(game.human.funds, 110)

    def test_bust_on_first_hand_moves_to_second(self):
        game = start_round(["8", "6", "8", "K", "K", "3", "K"])
        game.play(Action.SPLIT)
        game.play(Action.HIT)
        self.assertTrue(game.human.hands[0].is_bust())
        self.assertEqual(game.hand_index, 1)
        self.assertTrue(game.awaiting_human)

    def test_dealer_does_not_draw_when_both_hands_bust(self):
        game = start_round(["8", "6", "8", "K", "K", "K", "K", "K"])
        game.play(Action.SPLIT)
        game.play(Action.HIT)
        game.play(Action.HIT)
        run_until_stopped(game)
        self.assertEqual(len(game.dealer.cards), 2)
        self.assertEqual(game.human.funds, 80)

    def test_double_after_split(self):
        # Main 1 : 8+3+10 = 21, doublée. Main 2 : 8+10 = 18. Croupier : 19.
        game = start_round(["8", "9", "8", "K", "3", "10", "10"])
        game.play(Action.SPLIT)
        self.assertTrue(game.can_double())
        game.play(Action.DOUBLE)
        self.assertEqual(game.human.hands[0].bet, 20)
        game.play(Action.STAND)
        run_until_stopped(game)
        self.assertEqual(game.human.funds, 110)

    def test_split_aces_get_one_card_and_turn_ends(self):
        game = start_round(["A", "6", "A", "K", "5", "4", "2"])
        game.play(Action.SPLIT)
        self.assertFalse(game.awaiting_human)
        self.assertEqual([len(hand.cards) for hand in game.human.hands], [2, 2])

    def test_21_after_split_is_not_blackjack(self):
        # As + K : 21, payé 1 pour 1. Croupier : 18, deuxième main : 15 perd.
        game = start_round(["A", "8", "A", "K", "K", "4"])
        game.play(Action.SPLIT)
        run_until_stopped(game)
        first, second = game.human.hands
        self.assertFalse(first.is_blackjack())
        self.assertIs(first.outcome, Outcome.WIN)
        self.assertIs(second.outcome, Outcome.LOSE)
        self.assertEqual(game.human.funds, 100)

    def test_new_round_returns_to_one_hand(self):
        game = start_round(["8", "6", "8", "K", "K", "K", "K", "K"])
        game.play(Action.SPLIT)
        game.play(Action.HIT)
        game.play(Action.HIT)
        run_until_stopped(game)
        game.new_round()
        self.assertEqual(len(game.human.hands), 1)
        self.assertEqual(game.human.bet, 0)

    def test_bot_can_split_and_illegal_action_counts_as_stand(self):
        class SplittingBot(Bot):
            def decide(self, hand, dealer_upcard):
                return Action.SPLIT

        # Bot 1 (8, 8), Vous (K, Q), croupier (6, K), puis une carte par main du bot.
        game = BlackjackGame(2, shoe=RiggedShoe(["K", "8", "6", "Q", "8", "K", "3", "4"]))
        self.assertIs(game.players[0], game.human)
        bot = SplittingBot("Bot 1")
        game.players[1] = bot
        game.place_bet(10)
        game.deal()
        run_until_stopped(game)
        game.play(Action.STAND)
        run_until_stopped(game)
        self.assertIs(game.phase, Phase.ROUND_OVER)
        self.assertEqual(len(bot.hands), 2)


if __name__ == "__main__":
    unittest.main()
