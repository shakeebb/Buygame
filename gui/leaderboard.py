"""
Represents the leaderboard object for the client side of the game.
"""
import pygame

from common.player import Player
from common.gameconstants import *
from gui.display import Display


class Leaderboard(Display):
    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        self.name_font = pygame.font.SysFont("comicsans", 25, bold=True)
        self.score_font = pygame.font.SysFont("comicsans", 20)
        self.rank_font = pygame.font.SysFont("comicsans", 25)
        self.players: [Player] = []
        self.BORDER_THICKNESS = 5
        self.refresh_dims()

    def refresh_dims(self):
        super().refresh_dims()
        tmp_nm = LB_DISP_FMT % ("1", str('A').zfill(MAX_NAME_LENGTH), "200")
        fnt_sz = Display.get_target_fontsz(FONT_NAME, FONT_SIZE, True,
                                           tmp_nm, self.width)
        self.name_font = pygame.font.SysFont(FONT_NAME, fnt_sz, bold=True)
        self.score_font = pygame.font.SysFont(FONT_NAME, fnt_sz - 2)
        self.rank_font = pygame.font.SysFont(FONT_NAME, fnt_sz - 3)
        if VERBOSE:
            print("LB ht = %s, y = %s , y_margin = %s "
                  " width = %s " % (self.height, self.y, self.y_margin, self.width))

    def draw(self, win):
        scores = [(player.number, player.name, player.money) for player in self.players]
        scores.sort(key=lambda x: x[1], reverse=True)
        num_scores = len(scores)
        for i in range(LB_TOP_N):  # show only top 'n' scores
            if i % 2 == 0:
                color = Colors.LTR_GRAY.value
            else:
                color = Colors.LTS_GRAY.value
            sec_h = int(self.height / LB_TOP_N)
            pygame.draw.rect(win, color, (self.x, self.y + i * sec_h, self.width, sec_h))

            if i > num_scores or i >= len(scores):
                continue

            score = scores[i]
            # Draw text here
            # rank = self.rank_font.render("#" + str(i + 1), 1, (0, 0, 0))
            # win.blit(rank, (self.x + 5, self.y + i * self.HEIGHT + self.HEIGHT / 2 - rank.get_height() / 2))

            name = self.name_font.render(" #%s %s [%s]" % (score), True, (0, 0, 0))
            win.blit(name, (self.x, self.y + (i * sec_h) + (sec_h*0.35)))
            # win.blit(name, (self.x - name.get_width() / 2 + self.WIDTH / 2, self.y + i * self.HEIGHT + 10))

            # score = self.score_font.render("Score: " + str(score[1]), 1, (0, 0, 0))
            # win.blit(score, (self.x + 10, self.y + i * sec_h + 40))

        pygame.draw.rect(win, (0, 0, 0), (self.x, self.y, self.width, self.height),
                         self.BORDER_THICKNESS)

    def add_player(self, player):
        self.players.append(player)

    def remove_player(self, player):
        self.players.remove(player)

