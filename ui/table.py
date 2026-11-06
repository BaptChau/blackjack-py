import math
import time

import dearpygui.dearpygui as dpg

from enums.game import Action, Outcome, Phase
from ui import draw, theme
from ui.button import Button, ChipButton
from ui.draw import CARD_HEIGHT, CARD_WIDTH, money
from ui.theme import (
    CREAM, FELT, FELT_DARK, FELT_LINE, GOLD, GOLD_DIM, GREEN_WIN, HEIGHT, PANEL, RED_LOSE,
    WIDTH, WOOD, WOOD_LIGHT,
)
from ui.view import View

STEP_DELAY = 0.4

TABLE_CENTER = (WIDTH / 2, 30)
SEAT_RADIUS = (515, 470)
SEAT_ANGLE_STEP = 22
HAND_MAX_WIDTH = 180
SPLIT_HAND_MAX_WIDTH = 100
SPLIT_HAND_OFFSET = 54
CARD_OVERLAP = 30
DEALER_CARD_STEP = 72
DEALER_HAND_MAX_WIDTH = 420
SHOE_LEFT = 850

BAR_TOP = 700
CHIP_VALUES = (1, 5, 25, 100)
CHIP_RADIUS = 34
CHIP_GAP = 84
CHIPS_LEFT = 390

OUTCOME_LABELS = {
    Outcome.BLACKJACK: ("BLACKJACK", GOLD),
    Outcome.WIN: ("GAGNÉ", GREEN_WIN),
    Outcome.PUSH: ("ÉGALITÉ", CREAM),
    Outcome.LOSE: ("PERDU", RED_LOSE),
}


def seat_positions(count):
    positions = []
    for i in range(count):
        angle = math.radians((i - (count - 1) / 2) * SEAT_ANGLE_STEP)
        positions.append((
            TABLE_CENTER[0] + SEAT_RADIUS[0] * math.sin(angle),
            TABLE_CENTER[1] + SEAT_RADIUS[1] * math.cos(angle),
        ))
    return positions


class TableView(View):
    def __init__(self, scene, on_leave):
        super().__init__(scene)
        self.on_leave = on_leave
        self.game = None
        self.next_step_at = 0.0
        self.layer = None
        self._add_controls()

    # --- Mise en place ---

    def _draw_table(self, layer):
        cx = TABLE_CENTER[0]
        dpg.draw_rectangle((0, 0), (WIDTH, HEIGHT), fill=theme.BACKGROUND, color=theme.BACKGROUND, parent=layer)
        # Ellipses centrées sur le haut de la fenêtre : seule la moitié basse est visible.
        for rx, ry, fill, color, thickness in (
            (630, 684, WOOD, WOOD_LIGHT, 3),
            (604, 658, FELT, GOLD_DIM, 2),
            (584, 638, None, FELT_LINE, 1),
        ):
            options = {"fill": fill} if fill else {}
            dpg.draw_ellipse((cx - rx, -ry), (cx + rx, ry), color=color, thickness=thickness,
                             segments=128, parent=layer, **options)

        draw.text(layer, cx, 186, "LE BLACKJACK PAIE 3 POUR 2", 19, GOLD, "center")
        draw.text(layer, cx, 212, "Le croupier tire à 16 et reste à 17", 14, FELT_LINE, "center")

        # Sabot
        left, top = SHOE_LEFT, 44
        dpg.draw_rectangle((left + 8, top + 8), (left + 118, top + 78), fill=(0, 0, 0, 90), color=(0, 0, 0, 0), rounding=6, parent=layer)
        dpg.draw_rectangle((left, top), (left + 110, top + 70), fill=(26, 22, 20), color=GOLD_DIM, rounding=6, parent=layer)
        dpg.draw_rectangle((left + 8, top + 10), (left + 102, top + 60), fill=(128, 22, 34), color=GOLD, rounding=3, parent=layer)
        draw.text(layer, left + 55, top + 26, "SABOT", 15, CREAM, "center")

        dpg.draw_rectangle((0, BAR_TOP), (WIDTH, HEIGHT), fill=(14, 9, 6), color=(14, 9, 6), parent=layer)
        dpg.draw_line((0, BAR_TOP), (WIDTH, BAR_TOP), color=GOLD_DIM, thickness=2, parent=layer)

    def _add_controls(self):
        y = BAR_TOP + 22
        red = (150, 26, 38)
        green = (22, 110, 72)
        gold = (170, 126, 44)
        dark = (54, 44, 36)
        ink = (24, 16, 8)

        self.chip_buttons = [
            ChipButton(CHIPS_LEFT + i * CHIP_GAP, BAR_TOP + 50, CHIP_RADIUS, value,
                       lambda value=value: self._on_chip(value))
            for i, value in enumerate(CHIP_VALUES)
        ]
        self.clear_button = Button(780, y, 130, 56, "Effacer", dark, self._on_clear)
        self.deal_button = Button(926, y, 190, 56, "Distribuer", gold, self._on_deal, text_color=ink)
        self.hit_button = Button(474, y, 150, 56, "Tirer", green, lambda: self._on_action(Action.HIT))
        self.stand_button = Button(640, y, 150, 56, "Rester", red, lambda: self._on_action(Action.STAND))
        self.double_button = Button(806, y, 150, 56, "Doubler", gold, lambda: self._on_action(Action.DOUBLE), text_color=ink)
        self.split_button = Button(972, y, 150, 56, "Split", gold, lambda: self._on_action(Action.SPLIT), text_color=ink)
        self.next_button = Button(840, y, 280, 56, "Nouvelle manche", gold, self._on_next, text_color=ink)
        self.leave_button = Button(1136, y + 8, 124, 40, "Quitter", dark, self.on_leave)

        self.buttons = self.chip_buttons + [
            self.clear_button, self.deal_button, self.hit_button, self.stand_button,
            self.double_button, self.split_button, self.next_button, self.leave_button,
        ]

    # --- Boucle ---

    def enter(self, game):
        """Draws the table into the scene and seats `game` at it."""
        self.game = game
        self.next_step_at = 0.0
        self._draw_table(dpg.add_draw_layer(parent=self.scene))
        self.layer = dpg.add_draw_layer(parent=self.scene)
        self.refresh()

    def leave(self):
        self.game = None

    def tick(self):
        """Advances the automatic part of the game at a readable pace."""
        game = self.game
        if game is None or not game.is_automatic or time.monotonic() < self.next_step_at:
            return
        game.advance()
        self.next_step_at = time.monotonic() + STEP_DELAY
        self.refresh()

    # --- Commandes ---

    def _on_chip(self, value):
        self.game.place_bet(value)
        self.refresh()

    def _on_clear(self):
        self.game.clear_bet()
        self.refresh()

    def _on_deal(self):
        self.game.deal()
        self.refresh()

    def _on_action(self, action):
        self.game.play(action)
        self.next_step_at = time.monotonic() + STEP_DELAY
        self.refresh()

    def _on_next(self):
        self.game.new_round()
        self.refresh()

    # --- Rendu ---

    def refresh(self):
        dpg.delete_item(self.layer, children_only=True)
        self._draw_dealer()
        self._draw_seats()
        self._draw_status()
        self._draw_bar()
        self._sync_controls()
        self.draw_buttons(self.layer)

    def _sync_controls(self):
        game = self.game
        betting = game.phase is Phase.BETTING and not game.is_broke
        for button in self.chip_buttons:
            button.visible = betting
            button.enabled = button.value <= game.human.funds
        for button in (self.clear_button, self.deal_button):
            button.visible = betting
            button.enabled = game.human.bet > 0

        for button in (self.hit_button, self.stand_button, self.double_button, self.split_button):
            button.visible = game.awaiting_human
        self.double_button.enabled = game.can_double()
        self.split_button.enabled = game.can_split()

        self.next_button.visible = game.phase is Phase.ROUND_OVER

    def _draw_hand(self, cards, center_x, top, max_width, highlight=False):
        step = CARD_OVERLAP
        if len(cards) > 1:
            step = min(step, (max_width - CARD_WIDTH) / (len(cards) - 1))
        width = CARD_WIDTH + step * (len(cards) - 1)
        x = center_x - width / 2
        for i, card in enumerate(cards):
            draw.card_face(self.layer, x + i * step, top, card)
        if highlight:
            dpg.draw_rectangle((x - 4, top - 4), (x + width + 4, top + CARD_HEIGHT + 4),
                               color=GOLD, thickness=2, rounding=9, parent=self.layer)

    def _draw_dealer(self):
        game = self.game
        layer = self.layer
        cx = TABLE_CENTER[0]
        draw.text(layer, cx, 30, "CROUPIER", 15, GOLD, "center")
        dealer = game.dealer
        cards = dealer.cards
        step = DEALER_CARD_STEP
        if len(cards) > 1:
            step = min(step, (DEALER_HAND_MAX_WIDTH - CARD_WIDTH) / (len(cards) - 1))
        x = cx - (CARD_WIDTH + step * (len(cards) - 1)) / 2
        for i, card in enumerate(cards):
            if i == 1 and game.hole_hidden:
                draw.card_back(layer, x + i * step, 54)
            else:
                draw.card_face(layer, x + i * step, 54, card)
        if cards:
            draw.pill(layer, x - 42, 88, str(game.visible_dealer_value()), 16, CREAM, PANEL)

        remaining = len(game.shoe.cards)
        draw.text(layer, SHOE_LEFT + 55, 122, f"{remaining} cartes", 14, CREAM, "center")

    def _draw_seats(self):
        game = self.game
        positions = seat_positions(len(game.players))
        for player, (x, y) in zip(game.players, positions):
            self._draw_seat(player, x, y)

    def _draw_seat(self, player, x, y):
        game = self.game
        layer = self.layer
        is_human = player is game.human
        is_current = player is game.current_player

        ring = GOLD if is_current else (GOLD_DIM if is_human else FELT_LINE)
        dpg.draw_circle((x, y), 30, fill=FELT_DARK, color=ring, thickness=3 if is_current else 2, parent=layer)
        if player.bet > 0:
            draw.chip_stack(layer, x, y, 22, player.bet)

        self._draw_player_hands(player, x, y)

        name_color = GOLD if is_human else CREAM
        draw.text(layer, x, y + 36, player.name, 16, name_color, "center")
        draw.text(layer, x, y + 56, money(player.funds), 14, GOLD_DIM if not is_human else CREAM, "center")
        if player.bet > 0:
            draw.text(layer, x + 36, y - 8, money(player.bet), 13, CREAM)

    def _draw_player_hands(self, player, x, y):
        layer = self.layer
        split = len(player.hands) > 1
        offsets = (-SPLIT_HAND_OFFSET, SPLIT_HAND_OFFSET) if split else (0,)
        max_width = SPLIT_HAND_MAX_WIDTH if split else HAND_MAX_WIDTH
        top = y - 36 - CARD_HEIGHT

        for hand, offset in zip(player.hands, offsets):
            if not hand.cards:
                continue
            hand_x = x + offset
            is_active = split and hand is self.game.current_hand
            self._draw_hand(hand.cards, hand_x, top, max_width, highlight=is_active)
            draw.pill(layer, hand_x, y - 58, str(hand.get_value()), 14, GOLD if is_active else CREAM, PANEL)
            if hand.outcome is not None:
                label, color = OUTCOME_LABELS[hand.outcome]
                draw.pill(layer, hand_x, top - 28, label, 14, color, PANEL)

    def _status_message(self):
        game = self.game
        if game.is_broke:
            return "Vous n'avez plus de jetons : quittez la table pour rejouer"
        if game.phase is Phase.BETTING:
            return "Sabot mélangé. Faites vos jeux" if game.just_shuffled else "Faites vos jeux"
        if game.phase is Phase.DEALING:
            return "Les jeux sont faits, rien ne va plus"
        if game.awaiting_human:
            value = game.current_hand.get_value()
            if len(game.human.hands) > 1:
                return f"Main {game.hand_index + 1} : {value}"
            return f"À vous de jouer : {value}"
        if game.phase is Phase.PLAYERS:
            return f"{game.current_player.name} joue"
        if game.phase is Phase.DEALER:
            return "Le croupier joue"
        return self._result_message()

    def _result_message(self):
        human = self.game.human
        hands = human.hands
        if len(hands) == 1 and hands[0].outcome is Outcome.BLACKJACK:
            return f"Blackjack ! Vous gagnez {money(hands[0].bet * 1.5)}"
        net = sum(hand.payout for hand in hands) - human.bet
        if net > 0:
            return f"Vous gagnez {money(net)}"
        if net < 0:
            return f"Vous perdez {money(-net)}"
        return "Égalité : mise rendue"

    def _draw_status(self):
        draw.pill(self.layer, TABLE_CENTER[0], 244, self._status_message(), 18, CREAM, PANEL)

    def _draw_bar(self):
        game = self.game
        layer = self.layer
        draw.text(layer, 40, BAR_TOP + 16, "SOLDE", 13, GOLD_DIM)
        draw.text(layer, 40, BAR_TOP + 34, money(game.human.funds), 30, GOLD)
        draw.text(layer, 210, BAR_TOP + 16, "MISE", 13, GOLD_DIM)
        draw.text(layer, 210, BAR_TOP + 34, money(game.human.bet), 30, CREAM)
