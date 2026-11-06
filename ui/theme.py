import os

import dearpygui.dearpygui as dpg

WIDTH = 1280
HEIGHT = 800

BACKGROUND = (20, 13, 9)
WOOD = (74, 42, 22)
WOOD_LIGHT = (112, 66, 34)
FELT = (12, 84, 56)
FELT_DARK = (9, 66, 44)
FELT_LINE = (34, 124, 88)
GOLD = (222, 184, 92)
GOLD_DIM = (160, 130, 66)
CREAM = (244, 236, 214)
RED = (178, 30, 42)
INK = (24, 24, 28)
GREEN_WIN = (92, 214, 130)
RED_LOSE = (240, 96, 96)
PANEL = (10, 8, 6, 190)

FONT_SMALL_PX = 36
FONT_LARGE_PX = 96

# Georgia pour l'ambiance casino, sinon une serif du système.
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "C:/Windows/Fonts/georgiab.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]


# Les polices sont chargées grandes puis réduites : le texte reste net sur Retina.
class Fonts:
    small = None
    large = None


def load_fonts():
    path = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
    if path is None:
        return
    with dpg.font_registry():
        Fonts.small = dpg.add_font(path, FONT_SMALL_PX)
        Fonts.large = dpg.add_font(path, FONT_LARGE_PX)


def shade(color, factor):
    return tuple(min(255, int(channel * factor)) for channel in color[:3])


def window_theme():
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BACKGROUND)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
    return theme
