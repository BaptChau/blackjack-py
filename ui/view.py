from ui.button import Pointer


class View:
    """Page de l'application : des calques dans la scène et des boutons."""

    def __init__(self, scene):
        self.scene = scene
        self.buttons = []
        self.pointer = Pointer()

    def refresh(self):
        raise NotImplementedError

    def handle_mouse(self, pos, down):
        if self.pointer.update(self.buttons, pos, down):
            self.refresh()

    def draw_buttons(self, layer):
        for button in self.buttons:
            if button.visible:
                button.draw(layer, hovered=button is self.pointer.hovered)
