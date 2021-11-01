import pygame

from display import Display
from gameconstants import VERBOSE


class Inventory(Display):
    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells, size, rows, cols, color):
        super().__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        if VERBOSE:
            print("Inv: %s %s W %s" % (h_margin_cells, v_margin_cells, width_cells))
        self.rows = rows
        self.col = cols
        self.items = [[None for _ in range(self.rows)] for _ in range(self.col)]
        self.box_size = Display.TILE_SIZE * size
        self.border = 3
        self.color = color
        self.tilegroup = pygame.sprite.Group()
        self.refresh_dims()

    # draw everything
    def draw(self, win):
        # draw background

        pygame.draw.rect(win, self.color,
                         (self.x, self.y, (self.box_size + self.border) * self.col + self.border,
                          (self.box_size + self.border) * self.rows + self.border))
        for x in range(self.col):
            for y in range(self.rows):
                rect = (self.x + (self.box_size + self.border) * x + self.border,
                        self.y + (self.box_size + self.border) * y + self.border, self.box_size, self.box_size)
                pygame.draw.rect(win, (180, 180, 180), rect)

                if self.items[x][y]:

                    if self.items[x][y].clicked:
                        pos = pygame.mouse.get_pos()
                        self.items[x][y].rect.x = pos[0] - (self.items[x][y].rect.width / 2.4)
                        self.items[x][y].rect.y = pos[1] - (self.items[x][y].rect.height / 2.4)
                        break  # prevents more than one tile at a time
                    elif self.items[x][y].inBox(self):
                        self.items[x][y].rect.topleft = (self.x + (x * (self.box_size + self.border)), self.y)
                    else:
                        self.items[x][y] = None
        self.tilegroup.draw(win)
        # self.items[x][y].image = pygame.transform.scale(self.items[x][y].image, (100,100))

    # get the square that the mouse is over
    def Get_pos(self):
        mouse = pygame.mouse.get_pos()
        x = mouse[0] - self.x
        y = mouse[1] - self.y

        x = x // (self.box_size + self.border)
        y = y // (self.box_size + self.border)

        return (int(x), int(y))

    # add an item/s
    def Add(self, Item, xy):
        x, y = xy
        # item already there
        if self.items[x][y]:
            # if self.items[x][y].letter == Item.letter:
            #     print("same letter")
            #     print(Item.letter)
            # else:
            #     temp = self.items[x][y]
            #     self.items[x][y] = Item
            #
            #     print("different letters are ")
            #     return temp
            print("tile already there")
        else:
            self.items[x][y] = Item

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

    def createWord(self):
        x, y = (0, 0)
        word = ""
        for i in range(self.col - 1):
            x = i
            if self.items[x][y]:
                word += self.items[x][y].letter
        print(word)

    def refresh_dims(self):
        super().refresh_dims()
        # self.box_size -= (self.col * self.border)
        if VERBOSE:
            print("%s " % self.box_size)
