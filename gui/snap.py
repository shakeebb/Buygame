import itertools

import pygame

from common.logger import log
from gui.display import Display
from common.gameconstants import VERBOSE, Colors


class Inventory(Display):

    class Slot(pygame.sprite.Sprite):
        def __init__(self, x, y, width, height, fill_color=Colors.LTR_GRAY):
            super(Inventory.Slot, self).__init__()
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.fill_color = fill_color
            self.rect_dims = (self.x, self.y, self.width, self.height)
            self._layer = 3

        def draw(self, win):
            pygame.draw.rect(win, self.fill_color.value, self.rect_dims)

    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells, size, rows, cols,
                 display_dollar_value: bool = False,
                 border_color=Colors.BLACK, box_color=Colors.LTR_GRAY):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
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
        self.items: [[base.Tile]] = []
        # self.items: [[Tile]] = [[None for _ in range(cols)] for _ in range(rows)]
        self.inv_slots: [[Inventory.Slot]] = []
        for x, y in itertools.product(range(rows), range(cols)):
            if x >= len(self.inv_slots):
                self.inv_slots.append([])
            if x >= len(self.items):
                self.items.append([])

            self.items[x].append(None)
            self.inv_slots[x].append(
                Inventory.Slot(self.x + (self.box_size + self.border) * y + self.border,
                               self.y + (self.box_size + self.border) * x + self.border,
                               self.box_size, self.box_size,
                               self.box_color)
            )
        self.dv_font = pygame.font.SysFont("comicsans", 50)
        self.display_dollar_value = display_dollar_value
        self.dollar_value_txt = self.dv_font.render(f"", 1, (0, 0, 0))

        self._layer = 2
        self.refresh_dims()

    # draw everything
    def draw(self, win):
        # draw background

        pygame.draw.rect(win, self.border_color.value,
                         (self.x, self.y, (self.box_size + self.border) * self.col + self.border,
                          (self.box_size + self.border) * self.rows + self.border))
        for x in range(self.rows):
            for y in range(self.col):
                # rect = (self.x + (self.box_size + self.border) * y + self.border,
                #         self.y + (self.box_size + self.border) * x + self.border, self.box_size, self.box_size)
                # pygame.draw.rect(win, self.box_color.value, rect)

                if self.items[x][y] is not None:
                    from gui.base import Tile
                    __t: Tile = self.items[x][y]
                    if __t.clicked:
                        pos = pygame.mouse.get_pos()
                        self.items[x][y].rect.x = pos[0] - (self.items[x][y].rect.width / 2.4)
                        self.items[x][y].rect.y = pos[1] - (self.items[x][y].rect.height / 2.4)
                        __t.init = False
                        # break  # prevents more than one tile at a time
                    elif __t.init:
                        _s: Inventory.Slot = self.inv_slots[x][y]
                        __t.update_rect(_s.x, _s.y)
                    #     # __t.update_rect(self.x + ((self.box_size + self.border) * (y + 0.5)),
                    #     #                 self.rect[1] + INIT_TILE_SIZE + self.border + 5)
                    elif self.items[x][y].inBox(self):
                        # self.items[x][y].rect.topleft = (self.x + (x * (self.box_size + self.border)), self.y)
                        _s: Inventory.Slot = self.inv_slots[x][y]
                        self.items[x][y].rect.topleft = (_s.x, _s.y)
                # else:
                    #     self.items[x][y] = None
                else:
                    self.inv_slots[x][y].draw(win)

        win.blit(self.dollar_value_txt,
                 (self.x + (self.col * (self.box_size + self.border)) + self.border + 10,
                  self.y))

        # self.tile_group.draw(win)
        # self.items[x][y].image = pygame.transform.scale(self.items[x][y].image, (100,100))

    # get the square that the mouse is over
    def Get_pos(self):
        mouse = pygame.mouse.get_pos()
        x = mouse[0] - self.x
        y = mouse[1] - self.y

        x = x // (self.box_size + self.border)
        y = y // (self.box_size + self.border)

        return int(x), int(y)

    # add an item/s
    def Add(self, item, xy=None):
        import gui
        assert isinstance(item, gui.base.Tile)
        if xy is None:
            # find the next available slot
            for i, j in itertools.product(range(self.rows), range(self.col)):
                if self.items[i][j] is None:
                    self.items[i][j] = item
                    self.tile_group.add(item)
                    break
        else:
            x, y = xy
            # item already there
            # 'x' is col and 'y' is row
            if self.items[y][x] is not None:
                # if self.items[x][y].letter == Item.letter:
                #     print("same letter")
                #     print(Item.letter)
                # else:
                #     temp = self.items[x][y]
                #     self.items[x][y] = Item
                #
                #     print("different letters are ")
                #     return temp
                log("tile already there")
            else:
                # 'x' is col and 'y' is row
                self.items[y][x] = item
                self.tile_group.add(item)
        self.refresh_dollar_value()

    def remove_tile(self, item):
        import gui
        assert isinstance(item, gui.base.Tile)

        for i, j in itertools.product(range(self.rows), range(self.col)):
            from gui.base import Tile
            x: Tile = self.items[i][j]
            if x is not None and x.id == item.id:
                self.items[i][j] = None
                self.tile_group.remove(item)
        self.refresh_dollar_value()

    # check whether the mouse in in the grid
    def In_grid(self, x, y):
        # print(f" x is {x} \n y is {y}\n cols {self.col -1 }\n rows {self.rows - 1 }")
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
        assert row < len(self.items)
        word = ""
        for t in self.items[row]:
            word = word + t.letter if t is not None else word
        # log(word)
        return word

    def refresh_dims(self):
        super().refresh_dims()
        # self.box_size -= (self.col * self.border)
        if VERBOSE:
            print("%s " % self.box_size)

    def clear(self):
        for i in range(self.rows):
            for j in range(self.col):
                self.items[i][j] = None
        self.tile_group.empty()
        self.refresh_dollar_value()

    def contains_letter(self, letter: str) -> bool:
        from gui.base import Tile
        for r, c in itertools.product(range(self.rows), range(self.col)):
            item = self.items[r][c]
            if item is not None:
                assert isinstance(item, Tile)
                if item.letter == letter:
                    return True

        return False

    def refresh_dollar_value(self):
        if not self.display_dollar_value:
            return
        total = 0
        for i, j in itertools.product(range(self.rows), range(self.col)):
            if self.items[i][j] is not None:
                total += self.items[i][j].score
        if total > 0:
            total *= total
            self.dollar_value_txt = self.dv_font.render(f"${total}", 1, (0, 0, 0))
        else:
            self.dollar_value_txt = self.dv_font.render("", 1, (0, 0, 0))
