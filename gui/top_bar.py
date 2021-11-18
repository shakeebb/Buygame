"""
Top bar displaying information about round
"""
import pygame

from common.game import Game
from common.logger import log
from gui.display import Display
from common.gameconstants import *
from gui.button import TextButton
from gui.label import Label, MessageList


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
        self.blink = False
        from gui.base import GameUI
        self.gameui: GameUI = None
        self.refresh_dims()
        self.connect_status_color = Colors.YELLOW
        self.connect_text = "Start"
        self.connection_button = TextButton(self.xmargin() - 7,
                                            self.v_margin_cells + int(self.height_cells / 2) - 1,
                                            3, 2, self.connect_status_color, self.connect_text,
                                            self.connect_status_color)
        self.connection_button.change_font_size(15)
        self.server_msg = Label(self.xmargin() - 20,
                                self.v_margin_cells + int(self.height_cells / 2),
                                20, 2,
                                Align.RIGHT, 15)
        self.client_msgs = MessageList(self.h_margin_cells + self.width_cells - 19.5,
                                       self.v_margin_cells + 0.5,
                                       12, 3,
                                       5, 15)

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

        self.server_msg.draw(win)
        self.client_msgs.draw(win)
        if self.gameui is not None:
            if self.gameui.network.is_connected:
                self.set_connection_status(Colors.GREEN)
            else:
                self.set_connection_status(Colors.RED)
                # self.button = pygame.draw.rect(win, self.color, self.start_button_pos, 0)
                self.blink = True

        self.connection_button.set_color(self.connect_status_color)
        self.connection_button.set_text(self.connect_text)
        self.connection_button.draw(win)
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
            log("TopBar ht = %s, y = %s" % (self.height, self.y))

    def button_events(self):
        """
        handle all button press events here
        :return: None
        """
        mouse = pygame.mouse.get_pos()
        if self.connect_status_color is Colors.YELLOW and self.connection_button.click(*mouse):
            try:
                myGame = self.gameui.network.send(ClientMsg.Start.msg)
                if myGame is not None and self.gameui.network.is_connected:
                    self.gameui.set_game(myGame)
                    if self.gameui.game().ready:
                        color = Colors.GREEN
                        self.client_msgs.add_msg(f"Game is ready. %s players connected" %
                                                 len(self.gameui.game().getPlayers()),
                                                 Colors.NAVY_BLUE)
                    else:
                        color = Colors.ORANGE
                    self.set_connection_status(color, True)
                    pygame.event.post(pygame.event.Event(EV_POST_START))
            except Exception as e:
                log(e)
        elif self.connect_status_color is Colors.RED and self.connection_button.click(*mouse):
            try:
                self.gameui.network.reconnect()
                self.gameui.game = self.gameui.network.send(ClientMsg.Get.msg)
                self.set_connection_status(Colors.GREEN)
            except Exception as e:
                log(e)

    def set_connection_status(self, s: Colors, override: bool = False):
        if self.connect_status_color is not Colors.YELLOW or override is True:
            self.connect_status_color = s
            if s is Colors.GREEN:
                self.connect_text = "Connected"
            if s is Colors.ORANGE:
                self.connect_text = "Waiting"
            if s is Colors.RED:
                self.connect_text = "ReConnect"
