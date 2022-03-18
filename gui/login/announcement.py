from typing import Optional

import pygame

from common.gameconstants import *
from common.logger import logger
from gui.common.display import Display
from gui.common.fontmixin import FontMixin
from gui.common.subsurface import SubSurface


class Document(FontMixin, Display):
    def __init__(self, h, v, w, ht):
        FontMixin.__init__(self)
        Display.__init__(self, h, v, w, ht)
        self.para_y = self.y

    # def put_text(self, texts: [Optional[str]]):
    #     ht = self.para_y
    #     for line in texts:
    #


class StudyAnnouncement(FontMixin, SubSurface):
    def __init__(self):
        # super(StudyAnnouncement, self).__init__()
        FontMixin.__init__(self)
        SubSurface.__init__(self)
        self.set_font_size(14)
        self.set_num_chars_per_line(130)
        self._layer = SubSurface._SS_BASE_LAYER
        self.run = True

    def main(self, input_game=None):
        clock = pygame.time.Clock()
        from gui.gameui import GameUI
        assert input_game is None or isinstance(input_game, GameUI)
        g: GameUI = input_game
        logger.reset()
        while self.run:
            clock.tick(FPS)
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT or \
                        (event.type == KEYUP and event.key == K_ESCAPE):
                    self.run = False
                    pygame.quit()
                    quit()

            self.draw(events)

    def show_announcement(self):
        header_1 = "Study Announcement"
        para_1 = """You are being invited to participate in the Buyword game study on how creative capacity will
            affect performance outcomes.

            Participation in this study is completely voluntary; whether you participate in this study
            is completely up to you. If you choose not to participate, there will be no penalty of any
            kind. If you participate, you will get a chance to win a $50 Amazon Gift Card.
            The chance of winning a prize is approximately 1 in 50.
            The winner will be notified immediately by email and provided with the electronic gift card
            information. Also, if you show outstanding performance during the study and enter the top
            three performers list, you will receive an extra $50 Amazon Gift Card.

            If you agree to be in this study, you will be asked to do the following things:

            You will play a word game with another study participant. The game lasts approximately
            20 mins.
            """
        header_2 = "To Participate in the Study:"

        para_2 = """You can participate in the study according to your own schedule by using below link:

                  XXXX

                  If you have any problems, or questions, or want to know more about this study, please
                  contact Ipek Koparan, 269-501-39-01, ikoparan@bentley.edu

                  Thank you in advance for your participation!

                  Best,
                  """

        h1fs = self.render_line(header_1)
        p1fs = self.render_multiline_text(para_1)
        h2fs = self.render_line(header_2)
        p2fs = self.render_multiline_text(para_2)
        basex, basey = (self.x + (1.6 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE),
                        self.y + (0 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE)
                        )

        self.surface.blit(h1fs, (basex, basey))

        def show_para(para_lines, total):
            for fs, fs_ht in map(lambda x: (x[1], x[1].get_rect().height) if x is not None else (None, None),
                                 para_lines):
                if fs is None:
                    continue
                self.surface.blit(fs, (basex, basey + total))
                total += fs_ht
            return total

        tot_p1ht = show_para(p1fs, h1fs.get_rect().height)
        h2_pos = (basex, basey + tot_p1ht)
        self.surface.blit(h2fs, h2_pos)

        tot_p2ht = show_para(p2fs, h2_pos[1])

    def draw(self, events):
        super().draw(events)
        self.show_announcement()
        pygame.display.update()


if __name__ == '__main__':
    Display.init()

    sa = StudyAnnouncement()
    sa.main()
