"""
Top bar displaying information about round
"""
import pygame

from display import Display
from gameconstants import *


class TopBar(Display):
    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        self.word = "Temp Rack"
        self.round = 1
        self.max_round = 15
        self.round_font = pygame.font.SysFont("comicsans", 50)
        self.BORDER_THICKNESS = 5
        self.time = 60
        self.drawing = False
        self.refresh_dims()

    def draw(self, win):
        pygame.draw.rect(win, (0, 0, 0), (self.x, self.y, self.width, self.height), self.BORDER_THICKNESS)

        # draw round
        txt = self.round_font.render(f"Round {self.round} of {self.max_round}", 1, (0, 0, 0))
        win.blit(txt, (self.x + 10, self.y + self.height / 2 - txt.get_height() / 2))

        # draw underscores
        # if self.drawing:
        wrd = self.word
        # else:
        #     wrd = TopBar.underscore_text(self.word)
        txt = self.round_font.render(wrd, 1, (0, 0, 0))
        win.blit(txt,
                 (self.x + self.width / 2 - txt.get_width() / 2, self.y + self.height / 2 - txt.get_height() / 2 + 10))

        pygame.draw.circle(win, (0, 0, 0), (self.x + self.width - 50, self.y + round(self.height / 2)), 30,
                           self.BORDER_THICKNESS)
        timer = self.round_font.render(str(self.time), 1, (0, 0, 0))
        win.blit(timer,
                 (self.x + self.width - 50 - timer.get_width() / 2, self.y + self.height / 2 - timer.get_height() / 2))

    @staticmethod
    def underscore_text(text):
        new_str = ""

        for char in text:
            if char != " ":
                new_str += " _ "
            else:
                new_str += "   "

        return new_str

    def change_word(self, word):
        self.word = word

    def change_round(self, rnd):
        self.round = rnd

    def refresh_dims(self):
        super().refresh_dims()
        if VERBOSE:
            print("TopBar ht = %s, y = %s" % (self.height, self.y))
