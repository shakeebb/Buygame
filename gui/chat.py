"""
Represents the chat for the game.
"""
import pygame

from gui.gui_common.display import Display
from common.gameconstants import *


class Chat(Display):
    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells, game):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        self.txt_sz = 0
        self.refresh_dims()
        self.BORDER_THICKNESS = 5
        self.content = ["Hello"]
        self.typing = ""
        self.chat_font = pygame.font.SysFont("comicsans", 20)
        self.type_font = pygame.font.SysFont("comicsans", 30)
        self.CHAT_GAP = 20

    def refresh_dims(self):
        super().refresh_dims()
        # h_tm = (h * 0.02)
        # h_bm = (h * 0.02)
        # self.WIDTH = (1 / 8) * w
        # self.HEIGHT = (h - self.y_margin - h_tm - h_bm)
        # self.x = (w - (w * 0.02)) - self.WIDTH + self.x_margin
        # self.y = self.y_margin + h_tm
        self.txt_sz = self.height * 0.1
        if VERBOSE:
            print("Chat ht = %s, y = %s , y_margin = %s " % (self.height, self.y, self.y_margin))

    # def update_chat(self):
    #     self.content.append(self.typing)
    #     self.typing = ""

    def update_chat(self, msg=None):
        if msg is not None:
            self.content.append(msg)
        else:
            self.content.append(self.typing)
            self.typing = ""

    def draw(self, win):
        pygame.draw.rect(win, Colors.DIRTY_YELLOW.value,
                         pygame.Rect(self.x, self.y, self.width, self.height), 4)
        # pygame.draw.line(win, (0, 0, 0), (self.x, self.y - 40),
        #                  (self.x + self.WIDTH, self.y + 40), self.BORDER_THICKNESS)
        pygame.draw.rect(win, Colors.LT_GRAY.value, pygame.Rect(self.x + 4, self.y + self.height - self.txt_sz - 1,
                                                                self.width - 5, self.txt_sz - 1))

        while len(self.content) * self.CHAT_GAP > self.height - self.txt_sz - 20:
            self.content = self.content[:-1]

        for i, chat in enumerate(self.content):
            txt = self.chat_font.render(" - " + chat, 1, (0, 0, 0))
            win.blit(txt, (self.x + 8, 10 + self.y + i * self.CHAT_GAP))

        type_chat = self.type_font.render(self.typing, 1, (0, 0, 0))
        win.blit(type_chat, (self.x + 5, self.y + self.height - 17 - type_chat.get_height() / 2))

    def type(self, char):
        if char == "backspace":
            if len(self.typing) > 0:
                self.typing = self.typing[:-1]
        elif char == "space":
            self.typing += " "
        elif len(char) == 1:
            self.typing += char

        if len(self.typing) >= 25:
            self.typing = self.typing[:25]
