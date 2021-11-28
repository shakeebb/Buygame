"""
Stores interface for button and two concrete button classes
to be used in the UI.
"""
import pygame

from gui.display import Display
from common.gameconstants import *


class Button(Display):

    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells, on_display=True,
                 fill_color: Colors = Colors.LTR_GRAY,
                 border_color: Colors = Colors.BLACK, bg_color: Colors = Colors.WHITE):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
    # def __init__(self, x, y, width, height, color, border_color=(0, 0, 0)):
    #     self.x = x
    #     self.y = y
    #     self.height = height
    #     self.width = width
        self.bg_color = bg_color
        self.fill_color = fill_color
        self.border_color = border_color
        self.BORDER_WIDTH = 2
        self.on_display = on_display
        self.clear_on_next_draw = False

    def refresh_dims(self):
        pass

    def set_color(self, color: Colors, set_border=False):
        self.fill_color = color
        if set_border:
            self.border_color = self.fill_color

    def draw(self, win):
        if not self.on_display:
            if not self.clear_on_next_draw:
                # we have already cleared when button not in display
                return
            bc = self.bg_color.value
            fc = self.bg_color.value
            self.clear_on_next_draw = False
        else:
            bc = self.border_color.value
            fc = self.fill_color.value
        pygame.draw.rect(win, fc, (self.x, self.y, self.width, self.height), 0)
        pygame.draw.rect(win, bc, (self.x, self.y, self.width, self.height), 1)
        # pygame.draw.rect(win, fc, (
        #     self.x + self.BORDER_WIDTH, self.y + self.BORDER_WIDTH, self.width - self.BORDER_WIDTH * 2,
        #     self.height - self.BORDER_WIDTH * 2), 0)

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

    def show(self):
        self.on_display = True
        self.clear_on_next_draw = False

    def hide(self):
        self.on_display = False
        self.clear_on_next_draw = True


class TextButton(Button):
    def __init__(self, x, y, width, height, fill_color: Colors, text, border_color: Colors = Colors.BLACK):
        super().__init__(x, y, width, height, fill_color=fill_color, border_color=border_color)
        self.text = text
        self.text_font = pygame.font.SysFont("comicsans", 30)

    def change_font_size(self, size):
        self.text_font = pygame.font.SysFont("comicsans", size)

    def set_text(self, text: str):
        self.text = text

    def draw(self, win):
        super().draw(win)
        if not self.on_display:
            return
        txt = self.text_font.render(self.text, 1, (0, 0, 0))
        win.blit(txt, (self.x + self.width / 2 - txt.get_width() / 2, self.y + self.height / 2 - txt.get_height() / 2))

    def refresh_dims(self):
        fnt_sz = Display.get_target_fontsz(FONT_NAME, FONT_SIZE, True,
                                           self.text, self.width)
        self.text_font = pygame.font.SysFont("comicsans", fnt_sz)


class RadioButton(Button):

    def __init__(self, x, y, width, height, on_display=True, text_offset=(28, 1),
                 fill_color: Colors = Colors.LTR_GRAY,
                 font_color: Colors = Colors.BLACK,
                 border_color: Colors = Colors.BLACK,
                 check_color: Colors = Colors.BLACK):
        super().__init__(x, y, width, height, fill_color=fill_color, border_color=border_color)

    # def __init__(self, x, y, color=(230, 230, 230),
    #              outline_color=(0, 0, 0), check_color=(0, 0, 0),
    #              font_size=22, font_color=(0, 0, 0),
    #              text_offset=(28, 1), font='comicsans'):
        self.fill_color = fill_color
        self.border_color = border_color
        self.check_color = check_color
        self.text_font = pygame.font.SysFont("comicsans", 22)
        self.font_color = font_color
        self.to = text_offset
        self.options: [RadioButton.Option] = []
        self.on_display = on_display
        self.last_chosen_option: RadioButton.Option = None

    class Option:
        def __init__(self, radio, x, y, idnum, caption=""):
            self.rb: RadioButton = radio
            self.x = x + (INIT_TILE_SIZE/4)
            self.y = y + (idnum * INIT_TILE_SIZE) + (INIT_TILE_SIZE/4)
            self.caption = caption
            self.checked = False
            self.checkbox_obj = pygame.Rect(self.x, self.y, 12, 12)
            self.checkbox_outline = self.checkbox_obj.copy()
            self.idnum = idnum

        def render(self, surface):
            if self.checked:
                pygame.draw.circle(surface, self.rb.border_color.value, (self.x + 6, self.y + 6), 5)
                pygame.draw.circle(surface, self.rb.check_color.value, (self.x + 6, self.y + 6), 4)

            elif not self.checked:
                pygame.draw.circle(surface, self.rb.border_color.value, (self.x + 6, self.y + 6), 5)
                pygame.draw.circle(surface, self.rb.fill_color.value, (self.x + 6, self.y + 6), 4)
            self._draw_button_text(surface)

        def _draw_button_text(self, surface):
            self.font_surf = self.rb.text_font.render(self.caption, True, self.rb.font_color.value)
            w, h = self.rb.text_font.size(self.caption)
            self.font_pos = (self.x + self.rb.to[0], self.y + 12 / 2 - h / 2 +
                             self.rb.to[1])
            surface.blit(self.font_surf, self.font_pos)

        def click(self, x, y):
            # x, y = pygame.mouse.get_pos()
            # px, py, w, h = self.checkbox_obj
            # print(self.checkbox_obj.collidepoint(x, y))
            px, py, cw, ch = self.checkbox_obj
            w, h = self.rb.text_font.size(self.caption)
            # print(self.font_surf.get_rect().collidepoint(x, y))
            x_ur = px + cw + w + self.rb.to[0]
            y_lr = py - h
            y_ur = py + h
            # print(f"{px} {py} {cw} {ch} {w} {h} -- {x_ur} -- {x} -- {y_lr} {y_ur} {y}")
            if px < x < x_ur and y_lr < y < y_ur:
                if not self.checked:
                    self.mark_checked()
                return True
            return False

        def mark_checked(self):
            self.checked = True
            self.rb.last_chosen_option = self

        def mark_unchecked(self):
            self.checked = False

    def draw(self, surface):
        super().draw(surface)
        if not self.on_display:
            return
        for o in self.options:
            o.render(surface)

    def click(self, x, y):
        if not self.on_display:
            return
        # if event_object.type == pygame.MOUSEBUTTONDOWN:
        for o in self.options:
            if o.click(x, y):
                for de_sel in self.options:
                    de_sel.mark_unchecked() if de_sel.idnum != o.idnum else None
                self.last_chosen_option = o
                break

    def add_option(self, txt):
        self.options.append(RadioButton.Option(self, self.x, self.y, caption=txt, idnum=len(self.options)))
        self.options[0].mark_checked()

    def show(self):
        if self.on_display:
            # already on display
            return
        self.on_display = True
        for o in self.options:
            o.mark_unchecked()
        self.options[0].mark_checked()

    def hide(self):
        if not self.on_display:
            # already on no-display
            return
        self.on_display = False
        self.last_chosen_option = None

    def get_chosen_option_value(self) -> int:
        return self.last_chosen_option.idnum if self.last_chosen_option is not None else -1
