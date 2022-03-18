from typing import Optional

import pygame_widgets
import pygame

from common.gameconstants import *
from common.logger import logger, log
from gui.button import TextButton
from gui.gui_common.display import Display
from gui.gui_common.fontmixin import FontMixin
from gui.gui_common.subsurface import SubSurface
from pygame_widgets.textbox import TextBox


class InformedConsent(FontMixin, SubSurface):
    def __init__(self):
        SubSurface.__init__(self)
        FontMixin.__init__(self)
        self.iagree = False
        self.set_font_size(14)
        self.set_num_chars_per_line(130)
        self._layer = SubSurface._SS_BASE_LAYER
        self.run = True
        path = os.path.dirname(__file__)
        filename = os.path.join(path, "..", "tiles", "bentley-logo.jpg")
        try:
            bentley_logo = pygame.image.load(filename).convert()
            lr = bentley_logo.get_rect()
            self.image = pygame.transform.scale(bentley_logo, (lr.width // 2, lr.height // 2))
        except pygame.error:
            log("Unable to load: %s " % filename)
            raise SystemExit
        self.header = []
        self.section_pages = []
        self.sec_pos = 0
        self.initialize_user_consent_form()
        h_mrg, v_mrg = self.xmargin() - 12, self.ymargin() - 4
        self.prev_button = TextButton(h_mrg - (4 * TILE_ADJ_MULTIPLIER),
                                      v_mrg,
                                      7, 3, Colors.GREEN,
                                      "prev",
                                      visual_effects=True)
        self.next_button = TextButton(h_mrg,
                                      v_mrg,
                                      7, 3, Colors.GREEN,
                                      "next",
                                      visual_effects=True)
        self.user_sign: Optional[TextBox] = None

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
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse = self.mousexy()
                    self.mouse_down(mouse)

                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse = self.mousexy()
                    self.mouse_up(mouse)
                    pygame.event.clear([pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN, pygame.KEYUP])

            self.draw(events)

    def mouse_down(self, mouse):
        if self.next_button.click(*mouse):
            self.next_button.mouse_down()
            return
        elif self.prev_button.click(*mouse):
            self.prev_button.mouse_down()
            return

    def mouse_up(self, mouse):
        if self.next_button.click(*mouse):
            if self.iagree:
                self.submit_useragree()
                self.next_button.mouse_up()
                return
            if self.sec_pos < len(self.section_pages) - 1:
                self.sec_pos += 1
                self.prev_button.show()
                if self.sec_pos < len(self.section_pages) - 1:
                    self.iagree = False
                else:
                    self.next_button.set_text("submit")
                    self.iagree = True
            self.next_button.mouse_up()
        elif self.prev_button.click(*mouse):
            self.iagree = False
            self.next_button.set_text("next")
            self.sec_pos -= 1 if self.sec_pos > 0 else 0
            if self.sec_pos == 0:
                self.prev_button.hide()
            self.prev_button.mouse_up()

    def initialize_user_consent_form(self):
        heading = "INFORMED CONSENT FORM"
        subheading = "Buyword Game in Auction Context"

        sections = [
            (None, """You are invited to be in a research study investigating bidding 
                      decisions in auctions. We ask that you read this form and ask any 
                      questions you may have before agreeing to be in the study.

                      This study is being conducted by: Ipek Koparan, 
                      Management Department, 
                      Bentley University
                """),
            ("Background Information",
             """The purpose of this study is to: understand how creative capacity will affect 
                performance outcomes. 
                """
             ),
            ("Procedures:",
             """If you agree to be in this study, you would be asked to do the 
                following things:

                You will be randomly paired up with another person to play a word game. 
                During the game, you will construct words with the letter tiles. 
                Further details on how to play the game will be provided before the game. 
                Also, you can consult the game instructions anytime during the game through a help button. 

                The game can last 30 to 40 mins. You don’t have to leave after playing one round. 
                You can play multiple rounds.
                """
             ),
            ("Risks and Benefits of being in the Study",
             """The study does involve the following risks:
             
                There is no psychological or any other type of risks involved in this study.

                The benefits to participation are: 

                Other than helping us improve our understanding of theoretical concepts in 
                practical use, you will also benefit from participating in this study. 
                This study will help you practice your analytical thinking skills.
                """
             ),
            ("Confidentiality:",
             """The records of this study will be kept private. In any sort of report, we might 
                publish, we will not include any information that will make it possible to identify a subject. 
                Research records will be stored securely and only researchers will have access to the records.
                """
             ),
            ("Voluntary Nature of the Study:",
             """Participation in this study is voluntary. Your decision whether or not to participate will not 
             affect your current or future relations with Bentley University. If you decide to participate, 
             you are free to refuse to answer any question. You may also withdraw at any time without affecting 
             those relationships. 
             """
             ),
            ("Contacts and Questions:",
             """The researcher conducting this study is: Ipek Koparan. You may ask any questions you have now. 
                If you have questions later, you are encouraged to contact her at 
                Adamian 309, Cell= 269 501 3901, email= ikoparan@bentley.edu. 

                If you have any questions or concerns regarding this study and would like to talk to someone 
                other than the researcher, you are encouraged to contact 
                
                Susan Richman, Bentley’s IRB Chair, Bentley University, 
                175 Forest Street, Waltham, Massachusetts  02452, or GA_IRB@bentley.edu, or 781.891.2660.
                """
             ),
            ("Statement of Consent:",
             """I have read the above information, asked any questions I might have, and have received answers. 
                I consent to participate in the study.
                """
             )
        ]

        ft_head = self.custom_font(ft_sz=32, bold=True)
        ft_subh = self.custom_font(ft_sz=25)
        ft_h1 = self.custom_font(ft_sz=20, bold=True)

        heading = self.custom_render_line(ft_head, heading)
        subheading = self.custom_render_line(ft_subh, subheading)
        yoffset = (1 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE)
        centrx, topy = (self.width // 2, self.y - yoffset)

        self.header.append((heading, heading.get_rect(center=(centrx, topy))))
        shr = subheading.get_rect(
            center=(centrx,
                    topy + heading.get_rect().h))

        self.header.append((subheading, shr))

        basex, basey = self.x + (1 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE), topy + shr.y + yoffset

        def get_paginated_body():
            body_ = []
            tot_ht = 0
            for sh, sc in sections:
                if sh is not None:
                    hdg = self.custom_render_line(ft_h1, sh)
                    body_.append((len(sh), hdg, (basex, basey + tot_ht)))
                    tot_ht += hdg.get_rect().h
                for sc_l, sc_fs in self.render_multiline_text(sc):
                    body_.append((sc_l, sc_fs, (basex, basey + tot_ht)))
                    tot_ht += sc_fs.get_rect().h
                    if tot_ht > self.height - basey - (2 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE):
                        yield body_[:-1]
                        tot_ht = 0  # sc_fs.get_rect().h
                        body_ = body_[-1:]
            yield body_

        [self.section_pages.append(s) for s in get_paginated_body()]
        pass

    def draw_header(self):
        # bentley-logo
        self.surface.blit(self.image,
                          (.5 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE,
                           .5 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE,
                           self.image.get_width(),
                           self.image.get_height()))
        [self.surface.blit(h[0], h[1]) for h in self.header]

    def draw(self, events):
        super().draw(events)
        self.draw_header()
        self.prev_button.draw(self.surface)
        self.next_button.draw(self.surface)
        spg = self.section_pages[self.sec_pos]
        skip_starting_blanks = True
        for line in spg:
            if skip_starting_blanks and line[0] == 0:
                continue
            skip_starting_blanks = False
            self.surface.blit(line[1], line[2])
        # last page
        if self.sec_pos >= len(self.section_pages) - 1:
            l_coord = spg[-1][2]
            self.create_user_sign(*l_coord,
                                  font=self.font,
                                  colour=Colors.WHITE.value,
                                  borderColour=Colors.LTR_GRAY.value,
                                  textColour=Colors.BLACK.value,
                                  radius=0, borderThickness=1
                                  )
        elif self.user_sign is not None:
            self.user_sign.disable()
            self.user_sign.hide()
        if self.user_sign is not None:
            pygame_widgets.update(events)
        pygame.display.update()

    def submit_useragree(self):
        pass

    def create_user_sign(self, basex, lasty, **kwargs):
        input_texts = [
            ("Signature: ", "Date: "),
            ("Signature of Investigator: ", "Date: ")
        ]

        basey = lasty + (3 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE)
        acc_ht = 0
        pcw = self.get_pixel_offset("_")[0]
        tw, th = (14 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE), (1 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE)
        yoffset = INIT_TILE_SIZE
        for _i, it in enumerate(input_texts):
            lw = self.get_pixel_offset(it[0])[0]
            numspaces = ((50 * INIT_TILE_SIZE) - lw)//pcw
            part1 = it[0] + "_" * numspaces
            part2 = it[1] + "_" * 20
            sign = self.render_line(part1 + " " + part2)
            f1w, f1h = [(s1, s2 - s1) for s1, s2 in
                        zip(self.get_pixel_offset(it[0]), self.get_pixel_offset(part1))]
            self.surface.blit(sign, sign.get_rect(topleft=(basex, basey + acc_ht)))
            if _i == 0 and self.user_sign is None:
                self.user_sign = TextBox(self.surface, basex+lw+INIT_TILE_SIZE, basey-yoffset, tw, th, **kwargs)
            elif self.user_sign is not None:
                self.user_sign.enable()
                self.user_sign.show()
            acc_ht += f1h[0] + 2 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE


if __name__ == '__main__':
    Display.init()

    ic = InformedConsent()
    ic.main()
