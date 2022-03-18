import re

import pygame

from common.gameconstants import *


class FontMixin:
    def __init__(self):
        self.font = None
        self.font_name = "comicsans"
        self.color = Colors.BLACK
        self.font_size = 20
        self.num_chars_per_line = 80
        self.antialias = True
        self._refresh()

    def _refresh(self):
        self.font = pygame.font.SysFont(self.font_name, self.font_size)

    def set_font_size(self, sz):
        self.font_size = sz
        self._refresh()

    def set_font_name(self, name):
        self.font_name = name
        self._refresh()

    def set_num_chars_per_line(self, chars):
        self.num_chars_per_line = chars

    def set_font_color(self, color):
        self.color = color

    def get_font(self):
        return self.font

    def render_texts(self, text):
        return [self.font.render(t.strip().replace(LINE_CONT, '   '), True, self.color.value) for t in
                text.split(NL_DELIM)]

    def render_line(self, _t):
        return self.font.render(_t, True, self.color.value)

    def custom_font(self,
                    ft_name="",
                    ft_sz=0,
                    bold=False,
                    italic=False):
        ft_name = self.font_name if len(ft_name) == 0 else ft_name
        ft_sz = self.font_size if ft_sz == 0 else ft_sz
        return pygame.font.SysFont(ft_name, ft_sz, bold=bold, italic=italic)

    def custom_render_line(self, ft, _t, color=Colors.BLACK):
        return ft.render(_t, self.antialias, color.value)

    def render_multiline_text(self, text):
        chars = self.num_chars_per_line
        fs_lines: [pygame.surface.Surface] = []
        lines = map(lambda x: x.strip(), re.split('[\\n]+?', text))
        # print(list(lines))
        lw, lht = 0, 0

        tmp_str = []
        consecutive_lf = False
        # print("---begin----")
        for _l in lines:
            if len(_l) == 0:
                # print(''.join(tmp_str).strip()) if len(tmp_str) > 0 else None
                fs = self.render_line(''.join(tmp_str).strip()) if len(tmp_str) > 0 else None
                fs_lines.append((len(tmp_str), fs))
                # print(_l)
                fs_lines.append((len(_l), self.render_line(_l))) if not consecutive_lf else None
                tmp_str = []
                consecutive_lf = True
                continue

            consecutive_lf = False
            if (len(tmp_str) + len(_l)) < chars - 1:
                [tmp_str.append(_c) for _c in _l]
                tmp_str.append(' ')
                continue

            for _c in _l:
                if len(tmp_str) < chars - 1:
                    tmp_str.append(_c)
                    continue

                for i, ws in enumerate(tmp_str[::-1]):
                    if ws == ' ':
                        # print(''.join(tmp_str[:-i - 1]).strip())
                        fs_lines.append((len(tmp_str),
                                         self.render_line(''.join(tmp_str[:-i - 1]).strip())))
                        tmp_str = tmp_str[-i - 1:]
                        tmp_str.append(_c)
                        break
            tmp_str.append(' ')

        if len(tmp_str) > 0:
            # print(''.join(tmp_str).strip())
            fs_lines.append((len(tmp_str), self.render_line(''.join(tmp_str).strip())))

        # print("---end----")
        return fs_lines

    def get_pixel_offset(self, text):
        return self.font.size(text)
