import pygame
from pygame.surface import Surface

from common.gameconstants import *
from gui.snap import Inventory


class UITile(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, t_id, tile_sprites, letter='C',
                 box_size: int = 50,
                 score=None):
        self._layer = TILE_LAYER
        super(UITile, self).__init__()
        self.t_id = t_id
        self.all_tiles: list[list[Surface]] = tile_sprites
        # self.original = pygame.image.load(os.path.join("tiles", f"{letter}.png"))
        if WILD_CARD in letter:
            row = 5
            col = 3
        else:
            row = int((ord(letter) - 65) / 5)
            col = int((ord(letter) - 65) % 5)
        self.image = self.all_tiles[row][col]
        self.original = self.image
        # self.image = pygame.image.load(os.path.join("tiles", f"{letter}.png"))
        # self.size = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (int(box_size+2), int(box_size+2)))
        self.size = self.image.get_size()
        self.box_size = box_size
        self.clicked = False
        self.mouse_down_pos: pygame.Rect = None
        self.rect = self.image.get_rect()
        self.update_rect(xpos, ypos)
        self.score = score
        self.letter: str = letter
        self.inabox = False
        self.init = True
        self.base_slot: Inventory.Slot = None

    def __str__(self):
        return str(self.base_slot) if self.base_slot is not None else self.letter

    def draw(self, win: Surface):
        off = BTN_SH_OFFSET*10
        # win.blit(self.image, self.rect)
        pygame.draw.rect(win, Colors.RED.value, (self.rect.x+off, self.rect.y+off,
                                                     self.rect.width+off, self.rect.height+off),
                         10,
                         border_radius=10,
                         border_top_right_radius=BTN_CORNER_RAD,
                         border_bottom_right_radius=BTN_CORNER_RAD,
                         border_bottom_left_radius=BTN_CORNER_RAD)
        # pygame.draw.rect(win)

    def update_slot(self, slot):
        if self.base_slot is not None:
            self.base_slot.inv.remove_tile(self)
        self.base_slot = slot
        # self.rect.topleft = (self.base_slot.x, self.base_slot.y)
        self.rect.center = self.base_slot.rect.center
        self.clicked = False

    def return_to_base(self):
        self.rect.x, self.rect.y = (self.base_slot.x, self.base_slot.y)
        self.clicked = False
        tg = self.base_slot.inv.tile_group
        if tg.has(self):
            tg.change_layer(self, TILE_LAYER)

    def inBox(self, inventory):
        border = 3
        # print(f"Tile Position is {self.rect.x} and {self.rect.y}")
        x = self.rect.left - inventory.x
        y = self.rect.top - inventory.y
        x = x // (self.box_size + border)
        y = y // (self.box_size + border)
        # print(f"Tile Position is {x} and {y}")
        self.inabox = inventory.in_grid(x, y)
        return self.inabox

    def update_rect(self, xpos, ypos):
        # self.rect.x = xpos - self.rect.width / 2
        # self.rect.y = ypos - self.rect.height / 2
        self.rect.x = xpos
        self.rect.y = ypos
        __r = self.original.get_rect()
        __r.x = self.rect.x
        __r.y = self.rect.y

    def m_button_down(self):
        self.clicked = True
        self.mouse_down_pos = pygame.rect.Rect(*pygame.mouse.get_pos(), 10, 10)

    def get_target_inventory(self, game_ui):
        from gui.gameui import GameUI
        assert isinstance(game_ui, GameUI), f"{type(game_ui)}"
        current_inv_t = self.base_slot.inv.inv_type
        if current_inv_t == InventoryType.WORD_RACK:
            if self.letter == WILD_CARD:
                return game_ui.wc_rack
            else:
                return game_ui.tile_rack
        elif current_inv_t == InventoryType.TILE_RACK:
            return game_ui.word_rack
        elif current_inv_t == InventoryType.WILD_CARD_RACK:
            return game_ui.word_rack
        else:
            return self.base_slot.inv

    def m_button_up(self, new_mouse_pos):
        if self.mouse_down_pos.collidepoint(*new_mouse_pos):
            self.clicked = False
            self.mouse_down_pos = None
            return True
        return False
