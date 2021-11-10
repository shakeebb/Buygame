"""
Stores interface for button and two concrete button classes
to be used in the UI.
"""
import pygame

from gui.display import Display
from common.gameconstants import *


class Button(Display):

    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells,
                 color: Colors, border_color: Colors = Colors.BLACK):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
    # def __init__(self, x, y, width, height, color, border_color=(0, 0, 0)):
    #     self.x = x
    #     self.y = y
    #     self.height = height
    #     self.width = width
        self.color = color.value
        self.border_color = border_color.value
        self.BORDER_WIDTH = 2

    def refresh_dims(self):
        pass

    def set_color(self, color: Colors, set_border = False):
        self.color = color.value
        if set_border:
            self.border_color = self.color

    def draw(self, win):
        pygame.draw.rect(win, self.border_color, (self.x, self.y, self.width, self.height), 0)
        pygame.draw.rect(win, self.color, (
            self.x + self.BORDER_WIDTH, self.y + self.BORDER_WIDTH, self.width - self.BORDER_WIDTH * 2,
            self.height - self.BORDER_WIDTH * 2), 0)

    def click(self, x, y):
        """
        if user clicked on button
        :param x: float
        :param y: float
        :return: bool
        """

        if self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height:
            return True  # user clicked button

        return False


class TextButton(Button):
    def __init__(self, x, y, width, height, color: Colors, text, border_color: Colors = Colors.BLACK):
        super().__init__(x, y, width, height, color, border_color)
        self.text = text
        self.text_font = pygame.font.SysFont("comicsans", 30)

    def change_font_size(self, size):
        self.text_font = pygame.font.SysFont("comicsans", size)

    def set_text(self, text: str):
        self.text = text

    def draw(self, win):
        super().draw(win)
        txt = self.text_font.render(self.text, 1, (0, 0, 0))
        win.blit(txt, (self.x + self.width / 2 - txt.get_width() / 2, self.y + self.height / 2 - txt.get_height() / 2))

    def refresh_dims(self):
        fnt_sz = Display.get_target_fontsz(FONT_NAME, FONT_SIZE, True,
                                           self.text, self.width)
        self.text_font = pygame.font.SysFont("comicsans", fnt_sz)
