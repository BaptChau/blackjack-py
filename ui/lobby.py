import dearpygui.dearpygui as dpg

from model.game import MAX_PLAYERS, MIN_PLAYERS, NUM_DECKS
from ui import draw, theme
from ui.button import Button
from ui.theme import CREAM, FELT, FELT_DARK, FELT_LINE, GOLD, GOLD_DIM, HEIGHT, WIDTH, WOOD, WOOD_LIGHT
from ui.view import View

BUTTON_SIZE = 64
BUTTON_GAP = 14
BUTTON_TOP = 360


class LobbyView(View):
    def __init__(self, scene, on_start):
        super().__init__(scene)
        self.on_start = on_start
        self.selected = min(5, MAX_PLAYERS)
        self.count_buttons = {}
        self.layer = None
        self._add_buttons()

    def _add_buttons(self):
        counts = range(MIN_PLAYERS, MAX_PLAYERS + 1)
        total = len(counts) * BUTTON_SIZE + (len(counts) - 1) * BUTTON_GAP
        x = (WIDTH - total) // 2
        for count in counts:
            button = Button(x, BUTTON_TOP, BUTTON_SIZE, BUTTON_SIZE, str(count), FELT_DARK,
                            lambda value=count: self._select(value), rounding=32)
            self.count_buttons[count] = button
            self.buttons.append(button)
            x += BUTTON_SIZE + BUTTON_GAP

        self.buttons.append(Button(WIDTH // 2 - 150, 560, 300, 64, "Prendre place", (150, 26, 38),
                                   lambda: self.on_start(self.selected)))

    def enter(self):
        """Draws the page into the scene."""
        self._draw_background(dpg.add_draw_layer(parent=self.scene))
        self.layer = dpg.add_draw_layer(parent=self.scene)
        self._select(self.selected)

    def _draw_background(self, layer):
        center_x = WIDTH / 2
        dpg.draw_rectangle((0, 0), (WIDTH, HEIGHT), fill=theme.BACKGROUND, color=theme.BACKGROUND, parent=layer)
        dpg.draw_circle((center_x, HEIGHT / 2), 410, fill=WOOD, color=WOOD_LIGHT, thickness=6, segments=128, parent=layer)
        dpg.draw_circle((center_x, HEIGHT / 2), 390, fill=FELT, color=GOLD_DIM, thickness=2, segments=128, parent=layer)
        dpg.draw_circle((center_x, HEIGHT / 2), 370, color=FELT_LINE, thickness=1, segments=128, parent=layer)

        draw.text(layer, center_x, 145, "BLACKJACK", 76, GOLD, "center")
        draw.text(layer, center_x, 240, "CASINO ROYAL", 20, CREAM, "center")
        dpg.draw_line((center_x - 150, 276), (center_x + 150, 276), color=GOLD_DIM, thickness=1, parent=layer)
        draw.text(layer, center_x, 310, "Nombre de joueurs à la table", 24, CREAM, "center")
        draw.text(layer, center_x, 645,
                  f"{NUM_DECKS} jeux complets  ·  {NUM_DECKS * 52} cartes  ·  Le blackjack paie 3 pour 2",
                  16, GOLD_DIM, "center")

    def _select(self, count):
        self.selected = count
        for value, button in self.count_buttons.items():
            button.fill = GOLD if value == count else FELT_DARK
            button.text_color = (30, 20, 10) if value == count else CREAM
        self.refresh()

    def refresh(self):
        dpg.delete_item(self.layer, children_only=True)
        bots = self.selected - 1
        if bots == 0:
            summary = "Seul face au croupier"
        else:
            summary = f"Vous et {bots} bot{'s' if bots > 1 else ''}"
        draw.text(self.layer, WIDTH / 2, 462, summary, 22, CREAM, "center")
        self.draw_buttons(self.layer)
