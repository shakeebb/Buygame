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
        self.cleared = False

    def refresh_dims(self):
        pass

    def set_color(self, color: Colors, set_border=False):
        self.fill_color = color
        if set_border:
            self.border_color = self.fill_color

    def get_color(self):
        return self.fill_color

    def draw(self, win):
        if self.on_display:
            bc = self.border_color.value
            fc = self.fill_color.value
        elif not self.cleared:
            self.cleared = True
            bc = self.bg_color.value
            fc = self.bg_color.value
        else:
            return
        pygame.draw.rect(win, fc, (self.x, self.y, self.width, self.height), 0)
        pygame.draw.rect(win, bc, (self.x, self.y, self.width, self.height), 1)

    def click(self, x, y):
        """
        if user clicked on button
        :param x: float
        :param y: float
        :return: bool
        """
        if not self.on_display:
            return False

        if self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height:
            return True  # user clicked button

        return False

    def show(self):
        self.on_display = True
        self.cleared = False

    def hide(self):
        self.on_display = False
        self.cleared = False


class TextButton(Button):
    def __init__(self, x, y, width, height, fill_color: Colors, text, border_color: Colors = Colors.BLACK):
        super().__init__(x, y, width, height, fill_color=fill_color, border_color=border_color)
        self.text = text
        self.render_txt = self.text
        self.text_font = pygame.font.SysFont("comicsans", 30)
        self.blink = False
        self.blink_indicator_fps = 0

    def change_font_size(self, size):
        self.text_font = pygame.font.SysFont("comicsans", size)

    def set_text(self, text: str):
        self.text = text
        self.render_txt = text

    def set_blink(self, b):
        self.blink = b
        self.blink_indicator_fps = FPS if FPS > 30 else 30
        self.render_txt = self.text if not b else ""

    def draw(self, win):
        super().draw(win)
        if not self.on_display:
            return
        if self.blink:
            if self.blink_indicator_fps == 0:
                self.render_txt = self.text if len(self.render_txt) == 0 else ""
                self.blink_indicator_fps = FPS if FPS > 30 else 30
            else:
                self.blink_indicator_fps -= 1
        txt = self.text_font.render(self.render_txt, 1, (0, 0, 0))
        win.blit(txt, (self.x + self.width / 2 - txt.get_width() / 2, self.y + self.height / 2 - txt.get_height() / 2))

    def refresh_dims(self):
        fnt_sz = Display.get_target_fontsz(FONT_NAME, FONT_SIZE, True,
                                           self.text, self.width)
        self.text_font = pygame.font.SysFont("comicsans", fnt_sz)


class RadioButton(Button):

    def __init__(self, x, y, width, height,
                 on_option_click=None,
                 on_display=True,
                 text_offset=(28, 1),
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
        self.on_option_click = on_option_click

    class Option:
        def __init__(self, radio, x, y, idnum, caption=""):
            self.rb: RadioButton = radio
            self.x = x + (INIT_TILE_SIZE/(4*TILE_ADJ_MULTIPLIER))
            self.y = y + (idnum * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE) + (INIT_TILE_SIZE/(4*TILE_ADJ_MULTIPLIER))
            self.caption = caption
            self.checked = False
            self.checkbox_obj = pygame.Rect(self.x, self.y,
                                            12,
                                            12)
            self.checkbox_outline = self.checkbox_obj.copy()
            self.idnum = idnum

        def render(self, surface):
            offset = 6 * TILE_ADJ_MULTIPLIER
            if self.checked:
                pygame.draw.circle(surface, self.rb.border_color.value, (self.x + offset, self.y + offset),
                                   5)
                pygame.draw.circle(surface, self.rb.check_color.value, (self.x + offset, self.y + offset),
                                   4)

            elif not self.checked:
                pygame.draw.circle(surface, self.rb.border_color.value, (self.x + offset, self.y + offset),
                                   5)
                pygame.draw.circle(surface, self.rb.fill_color.value, (self.x + offset, self.y + offset),
                                   4)
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
                if self.on_option_click is not None:
                    self.on_option_click(o)
                break

    def add_option(self, txt):
        self.options.append(RadioButton.Option(self, self.x, self.y, caption=txt,
                                               idnum=len(self.options)))
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


class MessageBox(pygame.sprite.Sprite):
    MAX_LINE_LENGTH = 70

    def __init__(self, parent_width: int, parent_height: int, width: int, height: int,
                 msg: str,
                 ok_text: str,
                 in_display: bool = False, on_ok=None, color = Colors.RED):
        super(MessageBox, self).__init__()
        self.font = pygame.font.SysFont("comicsans", 17)
        self.f_color = color

        _msgs = []
        oneliner = ""
        # get rid of the hyphen prefix
        self.orig_msg = msg[1:]
        for m in self.orig_msg.split(NL_DELIM):
            if len(m) <= 0:
                continue
            oneliner += ' ' + m
            while len(oneliner) > MessageBox.MAX_LINE_LENGTH:
                line = oneliner[:MessageBox.MAX_LINE_LENGTH]
                _msgs.append(self.font.render(line,
                                              True, self.f_color.value))
                oneliner = oneliner[MessageBox.MAX_LINE_LENGTH:]
                continue
        # add the residual last line
        _msgs.append(self.font.render(oneliner, True, self.f_color.value))

        self.msgs = _msgs
        self.in_display = in_display
        self.w = (width * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE)
        self.h = (height * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE)
        self.x = (parent_width - self.w) // 2
        self.y = (parent_height - self.h) // 2
        self.fc = Colors.WHITE
        self.bc = Colors.NAVY_BLUE

        r_m = self.msgs[0]
        self.l_x = self.x + (self.w - r_m.get_width())/2
        self.l_y = self.y + ((self.h - r_m.get_height()) * 1/4)

        t_w = 3 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE
        t_h = 1 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE
        mid_x = self.x + (self.w - t_w)/2
        bottom_y = self.y + ((self.h - t_h)*3/4)
        self.ok_button = TextButton(mid_x//INIT_TILE_SIZE,
                                    bottom_y//INIT_TILE_SIZE,
                                    t_w//INIT_TILE_SIZE, t_h//INIT_TILE_SIZE,
                                    Colors.YELLOW, ok_text,
                                    Colors.YELLOW)
        self.on_ok = on_ok

    def show(self):
        self.in_display = True

    def destroy(self):
        self.in_display = False
        if self.on_ok is not None:
            self.on_ok()

    def button_events(self, x, y):
        if self.ok_button.click(x, y):
            self.in_display = False
            if self.on_ok is not None:
                self.on_ok()
            return True

        return False

    def draw(self, win: pygame.Surface):
        # if self.in_display:
        pygame.draw.rect(win, self.fc.value, (self.x, self.y, self.w, self.h), 0)
        pygame.draw.rect(win, self.bc.value, (self.x, self.y, self.w, self.h), 1)
        for i, s in enumerate(self.msgs):
            win.blit(s, (self.l_x, self.l_y + (i * 10 * TILE_ADJ_MULTIPLIER)))
        self.ok_button.draw(win)


class InputText:
    def __init__(self, x: int, y: int, prompt,
                 default: str,
                 in_focus: bool = False,
                 max_length = MAX_NAME_LENGTH):
        self.prompt = prompt
        self.text = default
        self.in_focus = in_focus
        self.max_length = max_length
        self.x = x
        self.y = y

    def __repr__(self):
        return self.text

    def set_text(self, txt):
        if txt is None:
            return
        self.text = txt

    def type(self, char):
        if char == "backspace":
            if len(self.text) > 0:
                self.text = self.text[:-1]
        elif char == "space":
            self.text += " "
        elif len(char) == 1:
            self.text += char

        if len(self.text) >= self.max_length:
            self.text = self.text[:self.max_length]

    def begin_input(self):
        self.in_focus = True

    def end_input(self):
        self.in_focus = False
        # self.settings[self.field] = self.text

    def draw(self, win: pygame.Surface):
        n = Display.name(self.prompt + self.text)
        if self.in_focus:
            txt_f = Display.name(self.prompt)
            _x, _y = (self.x + txt_f.get_width(), self.y + n.get_height())
            pygame.draw.line(win, Colors.BLACK.value,
                             (_x, _y),
                             (_x + n.get_width() - txt_f.get_width(), _y),
                             3)
        win.blit(n, (self.x, self.y))


