"""Primitives de dessin : texte, cartes, jetons. Tout est vectoriel, sans image."""
import math

import dearpygui.dearpygui as dpg

from enums.suits import Suit
from ui.theme import CREAM, FONT_LARGE_PX, FONT_SMALL_PX, Fonts, GOLD, INK, RED

CARD_WIDTH = 64
CARD_HEIGHT = 90

CHIP_COLORS = {
    1: ((232, 228, 216), (60, 60, 70), INK),
    5: ((176, 32, 40), CREAM, CREAM),
    25: ((26, 112, 66), CREAM, CREAM),
    100: ((28, 26, 30), GOLD, GOLD),
}


def money(amount):
    return f"{amount:.2f}".rstrip("0").rstrip(".") + " €"


def text(parent, x, y, string, size, color, anchor="left"):
    """Draws text; (x, y) is its top-left, top-center or top-right per `anchor`."""
    font, font_px = (Fonts.large, FONT_LARGE_PX) if size > 26 else (Fonts.small, FONT_SMALL_PX)
    if anchor != "left":
        width = (dpg.get_text_size(string, font=font) or [0])[0] * size / font_px
        x -= width / 2 if anchor == "center" else width
    item = dpg.draw_text((x, y), string, size=size, color=color, parent=parent)
    if font is not None:
        dpg.bind_item_font(item, font)


def pill(parent, x, y, string, size, color, fill):
    """Draws centered text inside a rounded badge."""
    width = (dpg.get_text_size(string, font=Fonts.small) or [0])[0] * size / FONT_SMALL_PX
    half = width / 2 + size * 0.55
    height = size * 1.45
    dpg.draw_rectangle(
        (x - half, y), (x + half, y + height), fill=fill, color=color, rounding=height / 2,
        thickness=1, parent=parent,
    )
    text(parent, x, y + size * 0.2, string, size, color, "center")


def _heart(parent, x, y, s, color):
    r = s * 0.27
    dpg.draw_circle((x - s * 0.24, y - s * 0.16), r, fill=color, color=color, parent=parent)
    dpg.draw_circle((x + s * 0.24, y - s * 0.16), r, fill=color, color=color, parent=parent)
    dpg.draw_triangle(
        (x - s * 0.49, y - s * 0.03), (x + s * 0.49, y - s * 0.03), (x, y + s * 0.5),
        fill=color, color=color, parent=parent,
    )


def _diamond(parent, x, y, s, color):
    dpg.draw_quad(
        (x, y - s * 0.52), (x + s * 0.4, y), (x, y + s * 0.52), (x - s * 0.4, y),
        fill=color, color=color, parent=parent,
    )


def _stem(parent, x, y, s, color):
    dpg.draw_triangle(
        (x, y + s * 0.05), (x + s * 0.2, y + s * 0.52), (x - s * 0.2, y + s * 0.52),
        fill=color, color=color, parent=parent,
    )


def _spade(parent, x, y, s, color):
    r = s * 0.25
    dpg.draw_triangle(
        (x, y - s * 0.52), (x + s * 0.47, y + s * 0.08), (x - s * 0.47, y + s * 0.08),
        fill=color, color=color, parent=parent,
    )
    dpg.draw_circle((x - s * 0.23, y + s * 0.1), r, fill=color, color=color, parent=parent)
    dpg.draw_circle((x + s * 0.23, y + s * 0.1), r, fill=color, color=color, parent=parent)
    _stem(parent, x, y, s, color)


def _club(parent, x, y, s, color):
    r = s * 0.24
    dpg.draw_circle((x, y - s * 0.26), r, fill=color, color=color, parent=parent)
    dpg.draw_circle((x - s * 0.26, y + s * 0.1), r, fill=color, color=color, parent=parent)
    dpg.draw_circle((x + s * 0.26, y + s * 0.1), r, fill=color, color=color, parent=parent)
    _stem(parent, x, y, s, color)


SUIT_DRAWERS = {
    Suit.HEARTS.value: _heart,
    Suit.DIAMONDS.value: _diamond,
    Suit.CLUBS.value: _club,
    Suit.SPADES.value: _spade,
}
RED_SUITS = {Suit.HEARTS.value, Suit.DIAMONDS.value}


def card_face(parent, x, y, card):
    color = RED if card.suit in RED_SUITS else INK
    dpg.draw_rectangle(
        (x + 2, y + 3), (x + CARD_WIDTH + 2, y + CARD_HEIGHT + 3),
        fill=(0, 0, 0, 90), color=(0, 0, 0, 0), rounding=7, parent=parent,
    )
    dpg.draw_rectangle(
        (x, y), (x + CARD_WIDTH, y + CARD_HEIGHT),
        fill=(250, 247, 238), color=(150, 146, 134), rounding=7, thickness=1, parent=parent,
    )
    text(parent, x + 6, y + 4, card.rank, 20, color)
    draw_suit = SUIT_DRAWERS[card.suit]
    draw_suit(parent, x + 13, y + 34, 14, color)
    draw_suit(parent, x + CARD_WIDTH - 24, y + CARD_HEIGHT - 28, 30, color)


def card_back(parent, x, y):
    dpg.draw_rectangle(
        (x + 2, y + 3), (x + CARD_WIDTH + 2, y + CARD_HEIGHT + 3),
        fill=(0, 0, 0, 90), color=(0, 0, 0, 0), rounding=7, parent=parent,
    )
    dpg.draw_rectangle(
        (x, y), (x + CARD_WIDTH, y + CARD_HEIGHT),
        fill=(250, 247, 238), color=(150, 146, 134), rounding=7, thickness=1, parent=parent,
    )
    left, top, right, bottom = x + 5, y + 5, x + CARD_WIDTH - 5, y + CARD_HEIGHT - 5
    dpg.draw_rectangle((left, top), (right, bottom), fill=(128, 22, 34), color=GOLD, rounding=4, parent=parent)
    mid_x, mid_y = (left + right) / 2, (top + bottom) / 2
    dpg.draw_quad(
        (mid_x, top + 8), (right - 8, mid_y), (mid_x, bottom - 8), (left + 8, mid_y),
        color=GOLD, thickness=1.5, parent=parent,
    )
    _diamond(parent, mid_x, mid_y, 20, GOLD)


def chip(parent, x, y, radius, value, dimmed=False):
    base, edge, label = CHIP_COLORS[value]
    if dimmed:
        base, edge, label = [tuple(c // 3 for c in color) for color in (base, edge, label)]
    dpg.draw_circle((x, y + 2), radius, fill=(0, 0, 0, 110), color=(0, 0, 0, 0), parent=parent)
    dpg.draw_circle((x, y), radius, fill=base, color=edge, thickness=1, parent=parent)
    for i in range(6):
        angle = math.tau * i / 6
        inner = radius * 0.8
        dpg.draw_line(
            (x + inner * math.cos(angle), y + inner * math.sin(angle)),
            (x + radius * math.cos(angle), y + radius * math.sin(angle)),
            color=edge, thickness=max(2, radius * 0.16), parent=parent,
        )
    dpg.draw_circle((x, y), radius * 0.68, color=edge, thickness=1, parent=parent)
    if radius >= 20:
        size = radius * 0.62
        text(parent, x, y - size * 0.55, str(value), size, label, "center")


def chip_stack(parent, x, y, radius, amount):
    """Draws an amount as a stack of chips, largest at the bottom."""
    chips = []
    for value in sorted(CHIP_COLORS, reverse=True):
        count, amount = divmod(amount, value)
        chips += [value] * int(count)
    for i, value in enumerate(chips[:6]):
        chip(parent, x, y - i * 4, radius, value)
