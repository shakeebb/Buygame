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

#
# class UIBag(Display):
#     def __init__(self, h_margin_cells, v_margin_cells, num_cells):
#         super().__init__(h_margin_cells, v_margin_cells, num_cells, num_cells)
#         path = os.path.dirname(__file__)
#         self.image = pygame.image.load(os.path.join(path, "tiles", "bag-4.png")).convert()
#         im_sz = num_cells * Display.TILE_SIZE
#         self.image = pygame.transform.scale(self.image, (im_sz, im_sz))
#         # self.image = pygame.transform.scale(
#         #     pygame.image.load(os.path.join("Tiles", "bag-icon.png")).convert(),
#         #     (100, 50))
#         self.image.set_colorkey(self.image.get_at((0, 0)))
#         self.rect = self.image.get_rect()
#         self.count = 100
#         self.refresh_dims()
#
#     def drawMe(self):
#         Display.surface().blit(self.image, self.rect)
#
#     def refresh_dims(self):
#         super().refresh_dims()
#         self.rect = self.image.get_rect()
#         self.rect.x = self.x
#         self.rect.y = self.y


if __name__ == "__main__":

    _reset: bool = False
    _restore: bool = False
    user = server = ""
    port = 0
    import re
    for i in range(len(sys.argv)):
        if re.match("-ur|--user-reset", sys.argv[i].lower().strip()):
            _reset = True
        elif re.match("-rs|--restore", sys.argv[i].lower().strip()):
            _restore = True
        elif re.match("-u[\b]*|--user=", sys.argv[i].lower().strip()):
            if sys.argv[i].strip() == "-u":
                i += 1 if i < len(sys.argv) - 1 else 0
                user = sys.argv[i]
            else:
                user = str(sys.argv[i]).split('=')[1]

        elif re.match("-s[\b]*|--server=", sys.argv[i].lower().strip()):
            if sys.argv[i].strip() == "-s":
                i += 1 if i < len(sys.argv) - 1 else 0
                server = sys.argv[i]
            else:
                server = str(sys.argv[i]).split('=')[1]
        elif re.match("-p[\b]*|--port=", sys.argv[i].lower().strip()):
            if sys.argv[i].strip() == "-p":
                i += 1 if i < len(sys.argv) - 1 else 0
                port = int(sys.argv[i])
            else:
                port = int(sys.argv[i]).split('=')[1]

    Display.init()
    _main_m = MainMenu(False, False)
    _main_m.controls[0].set_text(user if len(user) > 0 else None)
    _main_m.controls[1].set_text(server if len(server) > 0 else None)
    _main_m.controls[2].set_text(port if port > 0 else None)
    from gui.gameui import GameUI
    gui = GameUI(_main_m)
    gui.main()
