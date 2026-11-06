import dearpygui.dearpygui as dpg

from model.game import BlackjackGame
from ui import theme
from ui.lobby import LobbyView
from ui.table import TableView
from ui.theme import HEIGHT, WIDTH


class App:
    def __init__(self):
        with dpg.window(tag="root", no_title_bar=True, no_move=True, no_resize=True,
                        no_scrollbar=True, no_scroll_with_mouse=True):
            self.scene = dpg.add_drawlist(WIDTH, HEIGHT)
        dpg.bind_theme(theme.window_theme())
        dpg.set_primary_window("root", True)

        self.table = TableView(self.scene, on_leave=self.show_lobby)
        self.lobby = LobbyView(self.scene, on_start=self.show_table)
        self.view = None
        self.show_lobby()

    def show_lobby(self):
        self.table.game = None
        dpg.delete_item(self.scene, children_only=True)
        self.lobby.enter()
        self.view = self.lobby

    def show_table(self, num_players):
        dpg.delete_item(self.scene, children_only=True)
        self.table.enter(BlackjackGame(num_players))
        self.view = self.table

    def tick(self):
        pos = dpg.get_mouse_pos(local=False)
        down = dpg.is_mouse_button_down(dpg.mvMouseButton_Left)
        self.view.handle_mouse(pos, down)
        self.table.tick()


def run():
    dpg.create_context()
    theme.load_fonts()
    dpg.create_viewport(title="Blackjack", width=WIDTH, height=HEIGHT, resizable=False)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    # Les mesures de texte ne sont disponibles qu'une fois les polices chargées.
    dpg.render_dearpygui_frame()

    app = App()
    while dpg.is_dearpygui_running():
        app.tick()
        dpg.render_dearpygui_frame()
    dpg.destroy_context()
