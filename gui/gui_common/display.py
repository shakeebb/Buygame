import itertools
import os

import pygame
from pygame.event import Event
from pygame.font import Font

from common import gameconstants
from common.gameconstants import *
import ctypes
import platform


def get_tile_sz(_w, _h, sz):
    return _w // sz, _h // sz


def within_max_limits(p_h_c, p_v_c, p_tile_sz):
    # return 45 <= p_h_c <= 120 and 25 <= p_v_c <= 70 and 8 < p_tile_sz < 128
    # return p_h_c <= 120 and p_v_c <= 70 and p_tile_sz <= 1028
    return p_h_c <= 500 and p_v_c <= 250 and p_tile_sz <= 1028


def above_min_limits(p_h_c, p_v_c, p_tile_sz):
    # return 52 <= p_h_c and 29 <= p_v_c and 10 <= p_tile_sz
    return 52 <= p_h_c and 29 <= p_v_c and 8 <= p_tile_sz


class Display(pygame.sprite.Sprite):
    print_grid = DISPLAY_TILE_GRID_OUTPUT
    TILE_SIZE = INIT_TILE_SIZE

    class __disp__:
        def __init__(self):
            self.WIDTH = 800
            self.HEIGHT = 600
            dis_info = pygame.display.Info()  # You have to call this before pygame.display.set_mode()
            self.monitor_size = (dis_info.current_w, dis_info.current_h)
            self.window = pygame.display.set_mode((int(self.monitor_size[0] * 0.96), int(self.monitor_size[1] * 0.89)),
                                                  SURFACE_FLAGS)
            self.win_w = self.window.get_width()
            self.win_h = self.window.get_height()
            # self.window = pygame.display.set_mode((self.WIDTH, self.HEIGHT), FULLSCREEN)
            self.surface = self.window
            # self.surface = pygame.Surface([self.WIDTH, self.HEIGHT])
            print("screen %s x %s , window %s x %s, surface %s x %s" %
                  (
                      self.monitor_size[0], self.monitor_size[1],
                      self.window.get_width(), self.window.get_height(),
                      self.surface.get_width(), self.surface.get_height()
                  ))
            self.surface.fill(BG_COLOR.value)
            self.title_font = pygame.font.SysFont("comicsans", 120)
            self.name_font = pygame.font.SysFont("comicsans", 40)
            self.enter_font = pygame.font.SysFont("comicsans", 40)
            self.num_h_cells, self.num_v_cells = get_tile_sz(self.win_w, self.win_h, Display.TILE_SIZE)
            max_try = Display.TILE_SIZE / 2
            while True:
                max_try -= 1
                if max_try <= 0:
                    print("Window is either too small or too large to render the game")
                    pygame.quit()
                    quit()
                if within_max_limits(self.num_h_cells, self.num_v_cells, Display.TILE_SIZE) \
                        and above_min_limits(self.num_h_cells, self.num_v_cells, Display.TILE_SIZE):
                    break
                Display.TILE_SIZE += 2
                self.num_h_cells, self.num_v_cells = get_tile_sz(self.win_w, self.win_h, Display.TILE_SIZE)

            print("The grid h x v cells are %s x %s, TILE_SIZE=%s TILE_SIZE_MULTIPLIER=%s" %
                  (
                      self.num_h_cells, self.num_v_cells,
                      INIT_TILE_SIZE, TILE_ADJ_MULTIPLIER
                  ))
            self.grid = [[0 for _ in range(self.num_h_cells)] for _ in range(self.num_v_cells)]

        def compute_display_grid(self, p_w, p_h):
            tsz_1 = p_w // self.num_h_cells
            tsz_2 = p_h // self.num_v_cells
            new_tile_sz = tsz_1 if tsz_2 > tsz_1 else tsz_2
            h_cells, v_cells = get_tile_sz(p_w, p_h, new_tile_sz)
            if above_min_limits(h_cells, v_cells, new_tile_sz) and within_max_limits(h_cells, v_cells, new_tile_sz):
                Display.TILE_SIZE = new_tile_sz
                return True
            else:
                return False

    __i: __disp__ = None

    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells):
        self._layer = 1
        # super(Display, self).__init__()
        pygame.sprite.Sprite.__init__(self)
        self.h_margin_cells = h_margin_cells
        self.v_margin_cells = v_margin_cells
        self.width_cells = width_cells
        self.height_cells = height_cells
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        Display.refresh_dims(self)

    def xmargin(self):
        return self.h_margin_cells + self.width_cells

    def ymargin(self):
        return self.v_margin_cells + self.height_cells

    def refresh_dims(self):
        self.x, self.y = Display.coord(self.h_margin_cells, self.v_margin_cells)
        self.width, self.height = Display.coord(self.width_cells, self.height_cells)

    @classmethod
    def init(cls):
        os.environ['SDL_VIDEO_CENTERED'] = '1'  # You have to call this before pygame.init()
        if platform.system().lower() == 'windows':
            ctypes.windll.user32.SetProcessDPIAware()
        pygame.init()
        pygame.font.init()
        if cls.__i is None:
            cls.__i = cls.__disp__()

    @classmethod
    def show(cls):
        # frame = pygame.transform.scale(cls.__i.surface, (cls.__i.window.get_width(), cls.__i.window.get_height()))
        # cls.__i.window.blit(frame, frame.get_rect())
        # cls.__i.window.blit(cls.__i.surface, Display.dims())
        cls.__i.window.blit(pygame.transform.scale(cls.__i.surface, (cls.__i.win_w, cls.__i.win_h)), (0, 0))
        pygame.display.update()

    @classmethod
    def resize(cls, event: Event, post_rsz: lambda w, h: None):
        i = cls.__i
        is_feasible = i.compute_display_grid(event.w, event.h)
        _w = event.w if is_feasible else i.win_w
        _h = event.h if is_feasible else i.win_h
        i.window = pygame.display.set_mode((_w, _h), SURFACE_FLAGS)
        i.win_w = i.window.get_width()
        i.win_h = i.window.get_height()
        print("%s x %s" % (i.win_w, i.win_h))
        post_rsz(i.win_w, i.win_h)
        cls.print_grid = DISPLAY_TILE_GRID_OUTPUT

    @classmethod
    def surface(cls):
        return cls.__i.surface

    @classmethod
    def dims(cls):
        return cls.__i.win_w, cls.__i.win_h

    @staticmethod
    def ff(f: Font, *args):
        return f.render(*args)

    @classmethod
    def name(cls, text):
        return Display.ff(cls.__i.name_font, text, True, (0, 0, 0))

    @classmethod
    def title(cls, text):
        return Display.ff(cls.__i.title_font, text, True, (0, 0, 0))

    @classmethod
    def enter_prompt(cls, text):
        return Display.ff(cls.__i.enter_font, text, True, (0, 0, 0))

    @classmethod
    def get_target_fontsz(cls, font_name, init_sz, bold, max_txt, threshold):
        fnt_sz = init_sz

        def get_font_width(sz):
            name_font = pygame.font.SysFont(font_name, sz, bold=bold)
            return name_font.render(max_txt, True, Colors.BLACK.value).get_rect().width

        fnt_width = get_font_width(fnt_sz)
        while fnt_width > threshold:
            fnt_sz -= 1
            fnt_width = get_font_width(fnt_sz)

        if VERBOSE:
            print("Font_sz %s font_width %s  threshold_width %s" % (fnt_sz, fnt_width, threshold))
        return fnt_sz

    @classmethod
    def display_grid(cls):
        instance = cls.__i
        y, x = 0, 0
        if gameconstants.DISPLAY_TILE_GRID:
            for _h in range(0, instance.win_h, 3):
                for _w in range(0, instance.win_w, 3):
                    # pygame.draw.rect(instance.surface, Colors.LTS_GRAY.value, Rect(_w, _h,
                    #                                                                Display.TILE_SIZE,
                    #                                                                Display.TILE_SIZE),
                    #                  1)
                    pygame.draw.circle(instance.surface, Colors.BLACK.value, (_w, _h), 2)
                    if y < len(instance.grid) and x < len(instance.grid[y]):
                        instance.grid[y][x] = 1
                    x += 1
                y += 1
                x = 0

        if Display.print_grid:
            print("tile_sz - h x v cells: %s - %s x %s" % (
            Display.TILE_SIZE, instance.num_h_cells, instance.num_v_cells))
            # for _a in instance.grid:
            #     print(_a)
            Display.print_grid = False

    @classmethod
    def coord(cls, x_cell, y_cell):
        return (x_cell * Display.TILE_SIZE), (y_cell * Display.TILE_SIZE)

    @classmethod
    def num_horiz_cells(cls):
        return cls.__i.num_h_cells

    @classmethod
    def num_vert_cells(cls):
        return cls.__i.num_v_cells

    @classmethod
    def check_blink_onoff(cls, blink, blink_fps):
        if not blink:
            return False, blink_fps
        draw = True
        if FPS < blink_fps <= 1.4 * FPS:
            draw = False
            return draw, blink_fps + -1.3 * FPS if blink_fps >= 1.3 * FPS else 1
        else:
            return draw, blink_fps + 1
