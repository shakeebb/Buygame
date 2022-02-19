import itertools
from typing import Optional

import pygame

import common.tile
from common.logger import log
from gui.display import Display
from common.gameconstants import VERBOSE, Colors, SLOT_LAYER, INVENTORY_LAYER, TILE_LAYER, MOVING_TILE_LAYER, \
    InventoryType


class Inventory(Display):

    class Slot(pygame.sprite.Sprite):
        def __init__(self, inv, x, y, width, height, fill_color=Colors.LTR_GRAY):
            self._layer = SLOT_LAYER
            super(Inventory.Slot, self).__init__()
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.fill_color = fill_color
            self.rect_dims = (self.x, self.y, self.width, self.height)
            from gui.uiobjects import UITile
            self.slot_tile: Optional[UITile] = None
            self.rect = pygame.rect.Rect(*self.rect_dims)
            self.inv: Inventory = inv

        def __str__(self):
            return self.__repr__()

        def __repr__(self):
            return f"\"{self.inv}\" letter {self.slot_tile.letter}" if self.is_filled() \
                else "<empty>"

        def draw(self, win):
            pygame.draw.rect(win, self.fill_color.value, self.rect_dims)
            # if self.is_filled():
            #     if self.slot_tile.clicked:
            #         r = self.slot_tile.rect
            #         mx, my = pygame.mouse.get_pos()
            #         (r.x, r.y) = (mx - r.width/2.4, my - r.height/2.4)

        def add_or_move_tile(self, tile):
            from gui.uiobjects import UITile
            assert isinstance(tile, UITile), f"{type(tile)}"
            assert self.is_empty()

            # update the tile slot first, so that if
            # self.inv == tile.base_slot.inv, then add/remove is
            # just b/w slots. Also, tile.update_slot removes
            # from the same inv, so let it drop the tile from
            # the slot first.
            tile.update_slot(self)

            self.slot_tile = tile
            self.inv.tile_group.add(tile, layer=TILE_LAYER)
            self.inv.tile_group.change_layer(tile, TILE_LAYER)
            self.inv.refresh_dollar_value()
            return True

        def remove_tile(self):
            self.slot_tile = None

        def is_filled(self):
            return self.slot_tile is not None

        def is_empty(self):
            return self.slot_tile is None

    def __init__(self, inv_type: InventoryType, gameui,
                 h_margin_cells, v_margin_cells, width_cells, height_cells,
                 size, rows, cols,
                 display_dollar_value: bool = False,
                 border_color=Colors.BLACK, box_color=Colors.LTR_GRAY):
        self._layer = INVENTORY_LAYER
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        self.inv_type = inv_type
        from gui.gameui import GameUI
        self.gameui: GameUI = gameui
        if VERBOSE:
            log("Inv: %s %s W %s" % (h_margin_cells, v_margin_cells, width_cells))
        self.rows = rows
        self.col = cols
        self.box_size = Display.TILE_SIZE * size
        self.border = 3
        self.border_color = border_color
        self.box_color = box_color
        self.tile_group = pygame.sprite.LayeredUpdates()
        from gui import base
        # self.items: [[base.Tile]] = []
        # self.items: [[Tile]] = [[None for _ in range(cols)] for _ in range(rows)]
        self.slots_group = pygame.sprite.LayeredUpdates()
        self.inv_slots: [[Inventory.Slot]] = []
        for x, y in itertools.product(range(rows), range(cols)):
            if x >= len(self.inv_slots):
                self.inv_slots.append([])
            # if x >= len(self.items):
            #     self.items.append([])
            #
            # self.items[x].append(None)
            s = Inventory.Slot(self,
                               self.x + (self.box_size + self.border) * y + self.border,
                               self.y + (self.box_size + self.border) * x + self.border,
                               self.box_size, self.box_size,
                               self.box_color)
            self.inv_slots[x].append(s)
            self.slots_group.add(s, layer=SLOT_LAYER)
        self.dv_font = pygame.font.SysFont("comicsans", 50)
        self.display_dollar_value = display_dollar_value
        self.dollar_value_txt = self.dv_font.render(f"", 1, (0, 0, 0))

        self.refresh_dims()
        self.rect = pygame.rect.Rect(self.x, self.y, self.width, self.height)

    def __repr__(self):
        return str(self.inv_type)

    def __str__(self):
        return self.__repr__()

    def foreach_slot(self, f):
        for r_slots in self.inv_slots:
            for s in r_slots:
                f(s)

    def foreach_filled_slot(self, f):
        for r_slots in self.inv_slots:
            for s in r_slots:
                if s.is_filled():
                    f(s)

    def find_in_slots(self, f):
        for row, r_slots in enumerate(self.inv_slots):
            for col, s in enumerate(r_slots):
                if f(s):
                    return row, col
        return None

    def map_filled_slots(self, f):
        for r_slots in self.inv_slots:
            for s in r_slots:
                if s.is_filled():
                    yield f(s)

    # draw everything
    def draw(self, win):
        # draw background

        pygame.draw.rect(win, self.border_color.value,
                         (self.x, self.y, (self.box_size + self.border) * self.col + self.border,
                          (self.box_size + self.border) * self.rows + self.border))
        self.foreach_slot(lambda s: s.draw(win))
        self.tile_group.draw(win)

        # for x in range(self.rows):
        #     for y in range(self.col):
        #         # rect = (self.x + (self.box_size + self.border) * y + self.border,
        #         #         self.y + (self.box_size + self.border) * x + self.border, self.box_size, self.box_size)
        #         # pygame.draw.rect(win, self.box_color.value, rect)
        #
        #         if self.items[x][y] is not None:
        #             from gui.base import Tile
        #             __t: Tile = self.items[x][y]
        #             if __t.clicked:
        #                 pos = pygame.mouse.get_pos()
        #                 self.items[x][y].rect.x = pos[0] - (self.items[x][y].rect.width / 2.4)
        #                 self.items[x][y].rect.y = pos[1] - (self.items[x][y].rect.height / 2.4)
        #                 __t.init = False
        #                 # break  # prevents more than one tile at a time
        #             elif __t.init:
        #                 _s: Inventory.Slot = self.inv_slots[x][y]
        #                 __t.update_rect(_s.x, _s.y)
        #             #     # __t.update_rect(self.x + ((self.box_size + self.border) * (y + 0.5)),
        #             #     #                 self.rect[1] + INIT_TILE_SIZE + self.border + 5)
        #             elif self.items[x][y].inBox(self):
        #                 # self.items[x][y].rect.topleft = (self.x + (x * (self.box_size + self.border)), self.y)
        #                 _s: Inventory.Slot = self.inv_slots[x][y]
        #                 self.items[x][y].rect.topleft = (_s.x, _s.y)
        #         # else:
        #             #     self.items[x][y] = None
        #         else:
        #             self.inv_slots[x][y].draw(win)

        win.blit(self.dollar_value_txt,
                 (self.x + (self.col * (self.box_size + self.border)) + self.border + 10,
                  self.y))

        # self.tile_group.draw(win)
        # self.items[x][y].image = pygame.transform.scale(self.items[x][y].image, (100,100))

    # get the square that the mouse is over
    def get_pos(self):
        mouse = pygame.mouse.get_pos()
        x = mouse[0] - self.x
        y = mouse[1] - self.y

        x = x // (self.box_size + self.border)
        y = y // (self.box_size + self.border)

        return int(x), int(y)

    # add an item/s
    def add_tile(self, item, xy=None):
        from gui.uiobjects import UITile
        assert isinstance(item, UITile), f"{type(item)} not UITile type"
        if xy is None:
            # find the next available slot
            r, c = self.find_in_slots(lambda _s: _s.is_empty())
            slot = self.inv_slots[r][c]
            assert isinstance(slot, Inventory.Slot)
            slot.add_or_move_tile(item)
            self.tile_group.add(item, layer=TILE_LAYER)
        else:
            x, y = xy
            # item already there
            # 'x' is col and 'y' is row
            slot = self.inv_slots[y][x]
            assert isinstance(slot, Inventory.Slot)
            if slot.is_filled():
                # if self.items[x][y].letter == Item.letter:
                #     print("same letter")
                #     print(Item.letter)
                # else:
                #     temp = self.items[x][y]
                #     self.items[x][y] = Item
                #
                #     print("different letters are ")
                #     return temp
                log(f"{self.inv_slots[y][x].slot_tile.letter} tile already there")
                item.return_to_base()
                return False
            else:
                # 'x' is col and 'y' is row
                self.inv_slots[y][x].add_tile(item)
                self.tile_group.add(item)
        self.refresh_dollar_value()
        return True

    def remove_tile(self, item):
        from gui.uiobjects import UITile
        assert isinstance(item, UITile)

        rc = self.find_in_slots(lambda s: s.is_filled() and s.slot_tile.t_id == item.t_id)
        if rc is None:
            return
        r, c = rc
        self.inv_slots[r][c].remove_tile()
        self.tile_group.remove(item)
        self.refresh_dollar_value()

    # check whether the mouse in in the grid
    def in_grid(self, x, y):
        print(f" x is {x} \n y is {y}\n cols {self.col -1 }\n rows {self.rows - 1 }")
        if 0 > x or x > self.col - 1:
            # print("wawaa")
            return False
        if 0 > y or y > self.rows - 1:
            # print("wawaa")
            return False
        return True

    def returntome(self, tiles):
        x = self.x
        i = 0
        j = 1
        secondrowx = self.x
        secondrowy = self.y + self.box_size
        extrax = self.x - 120 / 800 * 1200
        extray = self.y
        extrasecondx = self.x - 120 / 800 * 1200

        for tile in tiles:

            if i < 4:
                tile.rect.topleft = (x + self.border, self.y + self.border)
                x += self.box_size + self.border
                i += 1
            elif i < 8 and i >= self.border:
                tile.rect.topleft = (secondrowx + self.border, secondrowy + self.border)
                secondrowx += self.box_size + self.border
                i += 1

            elif i >= 8 and i < 10:
                tile.rect.topleft = (extrax + self.border, extray + self.border)
                extrax += self.box_size + self.border
                i += 1
            elif i >= 10 and i < 12:
                tile.rect.topleft = (extrasecondx + self.border, extray + 57 / 600 * 800)
                extrasecondx += self.box_size + self.border
                i += 1
            elif i >= 12:
                break
            # print(i)
        return tiles

    def get_word(self, row=0) -> str:
        assert row < len(self.inv_slots)
        word = "".join(map(lambda s: s.slot_tile.letter if s.is_filled() else "",
                           self.inv_slots[row]))
        return word

    def refresh_dims(self):
        super().refresh_dims()
        # self.box_size -= (self.col * self.border)
        if VERBOSE:
            print("%s " % self.box_size)

    def clear(self):
        self.foreach_filled_slot(lambda s: s.remove_tile())
        self.tile_group.empty()
        self.refresh_dollar_value()

    def contains_letter(self, tile) -> bool:
        assert isinstance(tile, common.tile.Tile)
        svr_tile: common.tile.Tile = tile
        return self.find_in_slots(
            lambda s: s.is_filled() and s.slot_tile.t_id == svr_tile.get_tile_id()
        ) is not None

    def refresh_dollar_value(self):
        if not self.display_dollar_value:
            return
        # total = 0
        total = sum(self.map_filled_slots(lambda s: s.slot_tile.score))
        # itertools.accumulate(xx,
        #                      lambda t, v: t + v, initial=0)

        # for i, j in itertools.product(range(self.rows), range(self.col)):
        #     if self.items[i][j] is not None:
        #         total += self.items[i][j].score
        if total > 0:
            total *= total
            self.dollar_value_txt = self.dv_font.render(f"${total}", 1, (0, 0, 0))
            self.gameui.notify_inv_value(self, total)
        else:
            self.dollar_value_txt = self.dv_font.render("", 1, (0, 0, 0))
            self.gameui.notify_inv_value(self, total)
