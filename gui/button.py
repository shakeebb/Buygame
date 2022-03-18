"""
Stores interface for button and two concrete button classes
to be used in the UI.
"""
import copy
from typing import Optional

import pygame
from pygame.event import Event

from gui.gui_common.display import Display
from common.gameconstants import *


class Button(Display):

    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells, on_display=True,
                 visual_effects=False,
                 fill_color: Colors = Colors.LTR_GRAY,
                 border_color: Colors = Colors.LTS_GRAY, bg_color: Colors = Colors.WHITE):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        # def __init__(self, x, y, width, height, color, border_color=(0, 0, 0)):
        #     self.x = x
        #     self.y = y
        #     self.height = height
        #     self.width = width
        self._mouse_down = False
        self.bg_color = bg_color
        self.display_color = fill_color
        self.fill_color = fill_color
        self.border_color = border_color
        self.BORDER_WIDTH = 2
        self.on_display = on_display
        self.cleared = False
        self.enabled = True
        self.effects = visual_effects
        off = BTN_SH_OFFSET
        self.border_rect = pygame.Rect(self.x+off, self.y+off, self.width-(2*off), self.height-(2*off))
        self.mouse_event_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.button_rect = pygame.Rect(self.x+off, self.y+off, self.width-(2*off), self.height-(2*off))

    def refresh_dims(self):
        pass

    def set_color(self, color: Colors, set_border=False):
        self.fill_color = color
        if set_border:
            self.border_color = self.fill_color

    def get_color(self):
        return self.fill_color

    def draw(self, win):
        render_shadow = self.effects
        if self.on_display:
            bc = self.border_color.value
            fc = self.fill_color.value
        elif not self.cleared:
            self.cleared = True
            bc = self.bg_color.value
            fc = self.bg_color.value
            # if not on display, border color will clear
            render_shadow = False
        else:
            return

        off = BTN_SH_OFFSET
        pygame.draw.rect(win, fc, self.border_rect,
                         0,
                         BTN_CORNER_RAD)
        if render_shadow and self._mouse_down:
            pygame.draw.rect(win, Colors.GRAY.value, self.mouse_event_rect,
                             off,
                             BTN_CORNER_RAD + off)
            pygame.draw.rect(win, Colors.LTR_GRAY.value, self.mouse_event_rect,
                             2,
                             BTN_CORNER_RAD + off)
        elif render_shadow:
            pygame.draw.rect(win, Colors.LTS_GRAY.value, self.mouse_event_rect,
                             off,
                             BTN_CORNER_RAD + off)
        else:
            pygame.draw.rect(win, bc, self.mouse_event_rect,
                             off,
                             BTN_CORNER_RAD + off)

        pygame.draw.rect(win, fc, self.button_rect,
                         0,
                         BTN_CORNER_RAD)

    def click(self, x, y):
        """
        if user clicked on button
        :param x: float
        :param y: float
        :return: bool
        """
        if not self.on_display or not self.enabled:
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

    def enable(self):
        self.fill_color = self.display_color
        self.enabled = True

    def disable(self):
        self.fill_color = Colors.LTR_GRAY
        self.enabled = False

    def mouse_down(self):
        self._mouse_down = True

    def mouse_up(self):
        self._mouse_down = False


class TextButton(Button):
    def __init__(self, x, y, width, height,
                 fill_color: Colors, text,
                 visual_effects=False,
                 border_color: Colors = Colors.LTS_GRAY):
        super().__init__(x, y, width, height, visual_effects=visual_effects,
                         fill_color=fill_color, border_color=border_color)
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
                 option_offset=(.2, .2),
                 horizontal=False,
                 fill_color: Colors = Colors.LTR_GRAY,
                 font_color: Colors = Colors.BLACK,
                 border_color: Colors = Colors.LTS_GRAY,
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
        self.oo = option_offset
        self.options: [RadioButton.Option] = []
        self.on_display = on_display
        self.last_chosen_option: Optional[RadioButton.Option] = None
        self.on_option_click = on_option_click
        self.horizontal = horizontal

    class Option:
        def __init__(self, radio, x, y, idnum, caption="", show_caption=True):
            self.rb: RadioButton = radio
            if not self.rb.horizontal:
                self.x = x + (INIT_TILE_SIZE / (4 * TILE_ADJ_MULTIPLIER))
                self.y = y + ((idnum+self.rb.oo[0]) * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE) + \
                             (INIT_TILE_SIZE / (4 * TILE_ADJ_MULTIPLIER))
            else:
                adj = self.rb.oo[0] if idnum == 0 else idnum * self.rb.oo[1]
                self.x = x + (adj * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE) + \
                             (INIT_TILE_SIZE / (4 * TILE_ADJ_MULTIPLIER))
                self.y = y + (INIT_TILE_SIZE / (2 * TILE_ADJ_MULTIPLIER))
            self.caption = caption
            self.show_caption = show_caption
            self.checked = False
            self.checkbox_obj = pygame.Rect(self.x, self.y,
                                            12,
                                            12)
            # self.checkbox_outline = self.checkbox_obj.copy()
            self.idnum = idnum

        def draw(self, surface):
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
            if self.show_caption:
                self._draw_button_text(surface)

        def _draw_button_text(self, surface):
            self.font_surf = self.rb.text_font.render(self.caption,
                                                      True, self.rb.font_color.value)
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
                return True
            return False

        def mark_checked(self):
            self.checked = True

        def mark_unchecked(self):
            self.checked = False

    def make_copy(self, yoffset):
        new_self = copy.deepcopy(self)
        new_self.y += yoffset
        return new_self

    def draw(self, surface):
        super().draw(surface)
        if not self.on_display:
            return
        for o in self.options:
            o.draw(surface)

    def key_up(self, event: Event):
        mod = event.mod == pygame.KMOD_NONE
        if mod and (event.key == pygame.K_DOWN or event.key == pygame.K_TAB) \
                and \
                self.last_chosen_option.idnum != len(self.options) - 1:
            nxt = self.options[self.last_chosen_option.idnum + 1]
            self.handle_option_sel(nxt)
            return True
        elif (
                mod and event.key == pygame.K_UP
                or
                (
                        event.mod & pygame.KMOD_SHIFT and event.key == pygame.K_TAB
                )
        ) and \
                self.last_chosen_option.idnum != 0:
            prev = self.options[self.last_chosen_option.idnum - 1]
            self.handle_option_sel(prev)
            return True
        return False

    def click(self, x, y):
        if not self.on_display:
            return

        if not self.border_rect.collidepoint(x, y):
            return

        # if event_object.type == pygame.MOUSEBUTTONDOWN:
        for o in self.options:
            if o.click(x, y):
                self.handle_option_sel(o)
                break

    def handle_option_sel(self, o: Option):
        if self.last_chosen_option is not None:
            self.last_chosen_option.mark_unchecked()
        # for de_sel in self.options:
        #     de_sel.mark_unchecked() if de_sel.idnum != o.idnum else None
        o.mark_checked()
        self.last_chosen_option = o
        if self.on_option_click is not None:
            self.on_option_click(o)

    def add_option(self, txt, show_caption=True, default_sel=0):
        self.options.append(RadioButton.Option(self, self.x, self.y, caption=txt,
                                               show_caption=show_caption,
                                               idnum=len(self.options)))
        if default_sel == (len(self.options) - 1):
            self.last_chosen_option = self.options[default_sel]
            self.last_chosen_option.mark_checked()

    def reset(self):
        for o in self.options:
            o.mark_unchecked()

    def show(self):
        if self.on_display:
            # already on display
            return
        self.on_display = True
        self.handle_option_sel(self.options[0])

    def hide(self):
        if not self.on_display:
            # already on no-display
            return
        self.on_display = False
        # self.last_chosen_option = None

    def get_chosen_option_value(self) -> int:
        return self.last_chosen_option.idnum if self.last_chosen_option is not None else -1


class MessageBox(pygame.sprite.Sprite):
    MAX_LINE_LENGTH = 70

    def __init__(self, parent_width: int, parent_height: int, width: int, height: int,
                 msg: str,
                 ok_text: str,
                 in_display: bool = False, on_ok=None, color=Colors.RED,
                 blink=False):
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
        self.clear_field = pygame.Surface((self.w, self.h))

        r_m = self.msgs[0]
        self.l_x = self.x + (self.w - r_m.get_width()) / 2
        self.l_y = self.y + ((self.h - r_m.get_height()) * 1 / 4)

        t_w = 3 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE
        t_h = 1 * TILE_ADJ_MULTIPLIER * INIT_TILE_SIZE
        mid_x = self.x + (self.w - t_w) / 2
        bottom_y = self.y + ((self.h - t_h) * 3 / 4)
        self.ok_button = TextButton(mid_x // INIT_TILE_SIZE,
                                    bottom_y // INIT_TILE_SIZE,
                                    t_w // INIT_TILE_SIZE, t_h // INIT_TILE_SIZE,
                                    Colors.YELLOW, ok_text,
                                    visual_effects=False,
                                    border_color=Colors.YELLOW)
        self.on_ok = on_ok
        self.blink = blink
        self.blink_fps = FPS if blink else -1

    def show(self):
        self.in_display = True

    def destroy(self, win):
        self.in_display = False
        self.clear_field.fill(BG_COLOR.value)
        win.blit(self.clear_field, (self.x, self.y))
        if self.on_ok is not None:
            self.on_ok()

    def button_events(self, event: Event, x, y):
        if event.type == pygame.MOUSEBUTTONUP and self.ok_button.click(x, y):
            self.ok_button.mouse_up()
            self.in_display = False
            if self.on_ok is not None:
                self.on_ok()
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN and self.ok_button.click(x, y):
            self.ok_button.mouse_down()
            return True

        return False

    def draw(self, win: pygame.Surface):
        # if self.in_display:
        pygame.draw.rect(win, self.fc.value, (self.x, self.y, self.w, self.h), 0)
        pygame.draw.rect(win, self.bc.value, (self.x, self.y, self.w, self.h), 1)
        draw = True
        if self.blink:
            if FPS < self.blink_fps <= 1.4 * FPS:
                draw = False
                self.blink_fps += -1.3 * FPS if self.blink_fps >= 1.3 * FPS else 1
            else:
                self.blink_fps += 1

        if draw:
            for i, s in enumerate(self.msgs):
                win.blit(s, (self.l_x, self.l_y + (i * 10 * TILE_ADJ_MULTIPLIER)))

        self.ok_button.draw(win)


class InputText:
    def __init__(self, x: int, y: int, prompt,
                 default: str,
                 in_focus: bool = False,
                 max_length=MAX_NAME_LENGTH):
        self.p_text = prompt
        self.prompt = Display.name(prompt)
        self.p_len = len(prompt)
        self.text = default
        self.in_focus = in_focus
        self.max_length = max_length
        f = Display.name(' '.join([' ' for _ in range(self.max_length)]))
        self.clear_field = pygame.Surface((f.get_width(), f.get_height()))
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
        n = Display.name(self.text)
        pr = self.prompt.get_rect()
        _x, _y = (self.x + pr.width, self.y + pr.height + 10)
        if self.in_focus:
            pygame.draw.line(win, Colors.BLACK.value,
                             (_x, _y),
                             (_x + n.get_width(), _y),
                             3)
        else:
            pygame.draw.line(win, BG_COLOR.value,
                             (_x, _y),
                             (_x + self.clear_field.get_width(), _y),
                             3)

        self.clear_field.fill(BG_COLOR.value)
        win.blit(self.clear_field, (self.x + pr.width, self.y))
        win.blit(n, (self.x + pr.width, self.y))
        win.blit(self.prompt, (self.x, self.y))


class ProgressBar(Button):
    def __init__(self, x, y, width, height,
                 fill_color: Colors = Colors.LTR_GRAY,
                 border_color: Colors = Colors.LTS_GRAY):
        super().__init__(x, y, width, height, fill_color=fill_color, border_color=border_color)
        xx = {}
        # xx.__contains__()

    def draw(self, win):
        pygame.draw.rect(win, Colors.GREEN.value, (self.x, self.y, self.width, self.height), 4)
        pass

