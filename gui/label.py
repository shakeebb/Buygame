"""
Displays simple texts.
to be used in the UI.
"""
import collections

import pygame

from gui.gui_common.display import Display
from common.gameconstants import *


class Label(Display):

    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells,
                 align: Align = Align.CENTER,
                 font_sz: int = 12, color: Colors = Colors.BLACK, border_color: Colors = None):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        self.__text = "INITIAL TEXT"
        self.align: Align = align
        self.font_sz = font_sz
        self.color: Colors = color
        self.border_color = border_color
        self.font = pygame.font.SysFont("timesnewroman", self.font_sz, italic=True)
        self.__label_txt = self.font.render(self.__text, True, (0, 0, 0))
        self.v_margin_cells += (self.__label_txt.get_height() * TILE_ADJ_MULTIPLIER)
        self.__label_x = 0
        self.__label_y = 0
        self.refresh_dims()

    def set_text(self, text):
        self.__text = str(text[:80])
        self.__text = self.__text.rstrip().lstrip()
        self.__label_txt = self.font.render(self.__text, 1, self.color.value)
        self.refresh_dims()
        # log(len(self.__text))
        # log(f"%s %s %s" % (self.x, self.width, self.x + self.width / 2))

    def refresh_dims(self):
        if self.align == Align.CENTER:
            self.__label_x = self.x + self.width / 2 - self.__label_txt.get_width() / 2,
            self.__label_y = self.y + self.height / 2 - self.__label_txt.get_height() / 2 + 10
        elif self.align == Align.RIGHT:
            self.__label_x = self.x + self.width - self.__label_txt.get_width() - INIT_TILE_SIZE
            self.__label_y = self.y + self.height / 2 - self.__label_txt.get_height() / 2 + 10

    def draw(self, win):
        win.blit(self.__label_txt, (self.__label_x, self.__label_y))


class MessageList(Display):

    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells,
                 num_msgs: int,
                 line_spacing: int = 15,
                 font_sz: int = 12, bold_face: bool = False,
                 border_width: int = 1, border_color: Colors = Colors.BLACK):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        self.list = collections.deque(maxlen=num_msgs)
        self.line_spacing = line_spacing
        self.font = pygame.font.SysFont("comicsans", font_sz, bold=bold_face)
        self.border_color = border_color
        self.border_width = border_width
        self.refresh_dims()

    def add_msg(self, msg: str, color: Colors = Colors.BLACK):
        s = self.font.render(msg, True, color.value)
        self.list.append(s)

    def draw(self, win):
        pygame.draw.rect(win, self.border_color.value,
                         (self.x, self.y, self.width, self.height), self.border_width,
                         2, 2, 2, 2, 2)
        for i, m in enumerate(self.list):
            win.blit(m, (self.x + 10, self.y + (i * self.line_spacing)))
