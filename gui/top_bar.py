"""
Top bar displaying information about round
"""
import pygame

from common.game import Game, PlayerState
from common.player import Player
from common.logger import log
from gui.display import Display
from common.gameconstants import *
from gui.button import TextButton
from gui.label import Label, MessageList


class TopBar(Display):
    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        self.word = ""
        self.round = 1
        self.max_round = 15
        self.player_font = pygame.font.SysFont("comicsans", 40)
        self.round_font = pygame.font.SysFont("comicsans", 30)
        self.BORDER_THICKNESS = 5
        self.time = 60
        self.drawing = False
        self.blink = False
        from gui.gameui import GameUI
        self.gameui: GameUI = None
        self.refresh_dims()
        self.connection_button = TextButton(self.xmargin() - 7,
                                            self.v_margin_cells + int(self.height_cells / 2) - 1,
                                            3 * TILE_ADJ_MULTIPLIER, 2,
                                            Colors.YELLOW, "Init",
                                            visual_effects=False,
                                            border_color=Colors.YELLOW)
        self.connection_button.change_font_size(15)
        self.client_msgs = MessageList(self.h_margin_cells + (width_cells - 19 * TILE_ADJ_MULTIPLIER),
                                       self.v_margin_cells + 0.5,
                                       12 * TILE_ADJ_MULTIPLIER,
                                       3 * TILE_ADJ_MULTIPLIER,
                                       5, 15)
        adj = pygame.font.SysFont("timesnewroman", 14, italic=True). \
            render("ABCDEFZ", True, (0, 0, 0)).get_height()

        # eq = (((self.ymargin() * INIT_TILE_SIZE) - adj * TILE_ADJ_MULTIPLIER)//INIT_TILE_SIZE)
        self.server_msg = Label(self.xmargin() - (20 * TILE_ADJ_MULTIPLIER),
                                self.ymargin() - (1.5 * TILE_ADJ_MULTIPLIER),
                                20 * TILE_ADJ_MULTIPLIER, 1.5 * TILE_ADJ_MULTIPLIER,
                                Align.RIGHT, 14)

    def draw(self, win):
        pygame.draw.rect(win, (0, 0, 0), (self.x, self.y, self.width, self.height), self.BORDER_THICKNESS)

        # draw round
        plyr_txt = self.player_font.render(f"Player {self.gameui.player_name} ",
                                      True, Colors.BLACK.value)
        rnd_txt = self.round_font.render(f"Round {self.round}",
                                     True, Colors.BLACK.value)
        win.blit(plyr_txt, (self.x + 10, self.y + self.height / 4 - plyr_txt.get_height() / 4))
        win.blit(rnd_txt, (self.x + 10, self.y + (self.height + plyr_txt.get_height()) / 2 - rnd_txt.get_height() / 2))

        # draw underscores
        # if self.drawing:
        wrd = self.word
        # else:
        #     wrd = TopBar.underscore_text(self.word)
        txt = self.round_font.render(wrd, 1, (0, 0, 0))
        win.blit(txt,
                 (self.x + self.width / 2 - txt.get_width() / 2, self.y + self.height / 2 - txt.get_height() / 2 + 10))

        self.server_msg.draw(win)
        # self.client_msgs.draw(win)
        if self.gameui is not None:
            if self.gameui.network is not None and not self.gameui.network.is_connected:
                self.__set_connection_status(Colors.RED)
                # self.button = pygame.draw.rect(win, self.color, self.start_button_pos, 0)
        self.connection_button.draw(win)
        # pygame.draw.circle(win, (0, 0, 0), (self.x + self.width - 50, self.y + round(self.height / 2)), 30,
        #                    self.BORDER_THICKNESS)
        # timer = self.round_font.render(str(self.time), 1, (0, 0, 0))
        # win.blit(timer,
        #          (self.x + self.width - 50 - timer.get_width() / 2, self.y + self.height / 2 - timer.get_height() / 2))

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

    def mouse_down(self):
        pass

    def mouse_up(self):
        """
        handle all button press events here
        :return: None
        """
        mouse = pygame.mouse.get_pos()
        c = self.connection_button.get_color()
        if c is Colors.YELLOW and self.connection_button.click(*mouse):
            pass
            # try:
            #     myGame = self.gameui.network.send(ClientMsgReq.Start.msg)
            #     if myGame is not None and self.gameui.network.is_connected:
            #         self.gameui.set_game(myGame)
            #         if self.gameui.game().ready:
            #             color = Colors.GREEN
            #             _g: Game = self.gameui.game()
            #             self.client_msgs.add_msg(f"Game is ready. {len(_g.getPlayers())} players connected."
            #                                      f" Leader is {_g.leader + 1}",
            #                                      Colors.NAVY_BLUE)
            #         else:
            #             color = Colors.ORANGE
            #         self.set_connection_status(color, True)
            #         pygame.event.post(pygame.event.Event(EV_POST_START))
            # except Exception as e:
            #     log("Start message failed", e)
        elif c is Colors.RED and self.connection_button.click(*mouse):
            try:
                self.gameui.network.reconnect()
                player: Player = self.gameui.me()
                _g = self.gameui.network.send(ClientMsgReq.Get.msg +
                                              "notifications_received=" +
                                              str(len(player.notify_msg))
                                              )
                if _g is not None:
                    self.gameui.set_game(_g)
                elif self.gameui.network.is_connected:
                    self.__set_connection_status(Colors.ORANGE)
                else:
                    self.__set_connection_status(Colors.RED)
            except Exception as e:
                self.__set_connection_status(Colors.RED)
                log("User initiated reconnect failed", e)

    def set_connection_status(self, p: Player):
        color = Colors.WHITE
        if p.player_state == PlayerState.PLAY:
            color = Colors.GREEN
        elif p.player_state == PlayerState.WAIT or \
                p.player_state == PlayerState.INIT:
            color = Colors.YELLOW
        self.__set_connection_status(color)

    def __set_connection_status(self, s: Colors):
        self.connection_button.set_color(s, set_border=True)
        if s is Colors.YELLOW:
            self.connection_button.set_text("Wait")
            self.connection_button.set_blink(True)
        elif s is Colors.GREEN:
            self.connection_button.set_text("Play")
            self.connection_button.set_blink(False)
        elif s is Colors.ORANGE:
            self.connection_button.set_text("Connected")
            self.connection_button.set_blink(True)
        elif s is Colors.RED:
            self.connection_button.set_text("ReConnect")
            self.connection_button.set_blink(True)
