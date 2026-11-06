import unittest

from ui.button import Button, ChipButton, Pointer


class PointerTests(unittest.TestCase):
    def setUp(self):
        self.clicks = []
        self.first = Button(0, 0, 100, 50, "a", (0, 0, 0), lambda: self.clicks.append("first"))
        self.second = Button(200, 0, 100, 50, "b", (0, 0, 0), lambda: self.clicks.append("second"))
        self.buttons = [self.first, self.second]
        self.pointer = Pointer()

    def move(self, pos, down=False):
        return self.pointer.update(self.buttons, pos, down)

    def click(self, pos):
        self.move(pos)
        self.move(pos, down=True)
        self.move(pos)

    def test_click_fires_once(self):
        self.click((10, 10))
        self.assertEqual(self.clicks, ["first"])

    def test_holding_does_not_repeat(self):
        for _ in range(5):
            self.move((10, 10), down=True)
        self.assertEqual(self.clicks, [])

    def test_click_outside_does_nothing(self):
        self.click((500, 500))
        self.assertEqual(self.clicks, [])

    def test_press_then_release_elsewhere_cancels(self):
        self.move((10, 10), down=True)
        self.move((210, 10), down=True)
        self.move((210, 10))
        self.assertEqual(self.clicks, [])

    def test_drag_in_from_outside_does_not_click(self):
        self.move((500, 500), down=True)
        self.move((10, 10), down=True)
        self.move((10, 10))
        self.assertEqual(self.clicks, [])

    def test_disabled_and_hidden_buttons_ignore_clicks(self):
        self.first.enabled = False
        self.second.visible = False
        self.click((10, 10))
        self.click((210, 10))
        self.assertEqual(self.clicks, [])

    def test_hover_change_requests_redraw_once(self):
        self.assertTrue(self.move((10, 10)))
        self.assertFalse(self.move((11, 11)))
        self.assertTrue(self.move((500, 500)))

    def test_chip_is_round(self):
        chip = ChipButton(100, 100, 30, 5, lambda: None)
        self.assertTrue(chip.contains((100, 125)))
        self.assertFalse(chip.contains((72, 72)))


if __name__ == "__main__":
    unittest.main()
