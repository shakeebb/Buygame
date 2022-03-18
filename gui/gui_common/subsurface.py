import pygame

from common.gameconstants import *
from gui.gui_common.display import Display


class SubSurface(pygame.sprite.Sprite):
    _SS_BASE_LAYER = 10

    def __init__(self):
        super().__init__()
        self.scr_w, self.scr_h = Display.dims()
        self.x, self.y = self.scr_w // 11, self.scr_h // 11
        self.surface = pygame.Surface.subsurface(Display.surface(),
                                                 (self.x, self.y,
                                                  self.scr_w // 1.2, self.scr_h // 1.2)
                                                 )
        self.ss_init_x, self.ss_init_y = self.surface.get_offset()
        self.width, self.height = self.surface.get_size()

    def xmargin(self):
        return self.width // INIT_TILE_SIZE

    def ymargin(self):
        return self.height // INIT_TILE_SIZE

    def draw(self, events):
        self.surface.fill(Colors.WHITE.value)

    def mousexy(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # mouse_x, mouse_y = map(lambda cord: cord[0] - cord[1],
        #                        zip(mouse, (self.ss_init_x, self.ss_init_y)))
        return mouse_x - self.ss_init_x, mouse_y - self.ss_init_y
