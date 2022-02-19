import os

import pygame
import sys

from common.game import *
from common.logger import log
from gui.display import Display
from gui.main_menu import MainMenu
from common.gameconstants import *


class SpriteSheet:
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error:
            log("Unable to load: %s " % filename)
            raise SystemExit

    def crop_out_sprites(self, width: int = 128, height: int = 128):
        all_sprites = [[pygame.Surface([width, height]) for _ in range(5)] for _ in range(6)]
        for j in range(0, 6):
            for i in range(0, 5):
                surf = all_sprites[j][i]
                surf.blit(self.sheet, (0, 0), (i * width, j * height, width, height))
                pygame.draw.rect(surf, Colors.BLACK.value, (0, 0, width - 1, height - 1), 1)
        if VERBOSE:
            for x in all_sprites:
                for y in x:
                    print(y.get_size())
        return all_sprites


class UIBag(Display):
    def __init__(self, h_margin_cells, v_margin_cells, num_cells):
        super().__init__(h_margin_cells, v_margin_cells, num_cells, num_cells)
        path = os.path.dirname(__file__)
        self.image = pygame.image.load(os.path.join(path, "tiles", "bag-4.png")).convert()
        im_sz = num_cells * Display.TILE_SIZE
        self.image = pygame.transform.scale(self.image, (im_sz, im_sz))
        # self.image = pygame.transform.scale(
        #     pygame.image.load(os.path.join("Tiles", "bag-icon.png")).convert(),
        #     (100, 50))
        self.image.set_colorkey(self.image.get_at((0, 0)))
        self.rect = self.image.get_rect()
        self.count = 100
        self.refresh_dims()

    def drawMe(self):
        Display.surface().blit(self.image, self.rect)

    def refresh_dims(self):
        super().refresh_dims()
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        log("Provide user name as the first argument")
        sys.exit(1)
    mm = MainMenu(False, False)
    mm.controls[0].text = sys.argv[1]
    if len(sys.argv) > 2:
        mm.controls[1].text = sys.argv[2]
    from gui.gameui import GameUI
    gui = GameUI(mm)
    gui.handshake()
    gui.main()
