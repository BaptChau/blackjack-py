"""Boutons dessinés à la main et lecture de la souris.

Un drawlist capte la souris sur toute sa surface : aucun widget DearPyGui posé
dessus ne recevrait de clic. Les boutons font donc partie du dessin, et les
clics sont détectés en comparant la position de la souris à leur zone.
"""
import math

import dearpygui.dearpygui as dpg

from ui import draw
from ui.theme import CREAM, GOLD, shade

DISABLED_FILL = (46, 44, 40)
DISABLED_TEXT = (120, 116, 108)
DISABLED_BORDER = (80, 76, 70)


class Button:
    def __init__(self, x, y, width, height, label, fill, on_click, text_color=CREAM, rounding=10):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.fill = fill
        self.on_click = on_click
        self.text_color = text_color
        self.rounding = rounding
        self.visible = True
        self.enabled = True

    @property
    def is_active(self):
        return self.visible and self.enabled

    def contains(self, pos):
        return (self.x <= pos[0] <= self.x + self.width
                and self.y <= pos[1] <= self.y + self.height)

    def draw(self, layer, hovered):
        if not self.enabled:
            fill, text_color, border = DISABLED_FILL, DISABLED_TEXT, DISABLED_BORDER
        else:
            fill = shade(self.fill, 1.25) if hovered else self.fill
            text_color, border = self.text_color, GOLD
        dpg.draw_rectangle(
            (self.x, self.y), (self.x + self.width, self.y + self.height),
            fill=fill, color=border, thickness=2, rounding=self.rounding, parent=layer,
        )
        size = 20
        draw.text(layer, self.x + self.width / 2, self.y + (self.height - size * 1.15) / 2,
                  self.label, size, text_color, "center")


class ChipButton(Button):
    def __init__(self, x, y, radius, value, on_click):
        super().__init__(x - radius, y - radius, radius * 2, radius * 2, "", None, on_click)
        self.center = (x, y)
        self.radius = radius
        self.value = value

    def contains(self, pos):
        return math.dist(pos, self.center) <= self.radius

    def draw(self, layer, hovered):
        x, y = self.center
        draw.chip(layer, x, y, self.radius, self.value, dimmed=not self.enabled)
        if hovered and self.enabled:
            dpg.draw_circle((x, y), self.radius + 3, color=GOLD, thickness=2, parent=layer)


class Pointer:
    """Transforme la position et l'état de la souris en survols et en clics."""

    def __init__(self):
        self.hovered = None
        self.pressed = None
        self.was_down = False

    def update(self, buttons, pos, down):
        """Fires `on_click` on release; returns True if the hover needs a redraw."""
        target = next((b for b in buttons if b.is_active and b.contains(pos)), None)
        hover_changed = target is not self.hovered
        self.hovered = target

        just_pressed = down and not self.was_down
        just_released = self.was_down and not down
        self.was_down = down

        if just_pressed:
            self.pressed = target
        elif just_released:
            clicked = target is not None and target is self.pressed
            self.pressed = None
            if clicked:
                # `on_click` redessine, ou change de page : plus rien à faire ici.
                target.on_click()
                return False
        return hover_changed
