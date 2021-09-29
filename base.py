import os

from pygame.locals import *

import pygame
import sys
from bottom_bar import BottomBar
from chat import Chat
from leaderboard import Leaderboard
from player import Player
from snap import Inventory
from top_bar import TopBar


class Game:
    FPS = 30  # frames per second, the general speed of the program
    # WINDOWWIDTH = 800 # size of window's width in pixels
    # WINDOWHEIGHT = 600 # size of windows' height in pixels
    #             R    G    B
    global COLORS
    COLORS = {
        "GRAY": (100, 100, 100),
        "NAVYBLUE": (60, 60, 100),
        "WHITE": (255, 255, 255),
        "RED": (255, 0, 0),
        "GREEN": (0, 255, 0),
        "BLUE": (0, 0, 255),
        "YELLOW": (255, 255, 0),
        "ORANGE": (255, 128, 0),
        "PURPLE": (255, 0, 255),
        "CYAN": (0, 255, 255)
    }

    BGCOLOR = COLORS["BLUE"]

    def __init__(self):
        global COLORS
        pygame.font.init()
        self.tileID = 0
        self.WIDTH = 1200
        self.HEIGHT = 800
        self.win = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.leaderboard = Leaderboard(self.WIDTH * 10 / 800, self.HEIGHT * 75 / 600)
        self.inventory = Inventory(self.WIDTH * 0.08, self.HEIGHT * 300 / 600, 75, 1, 10, COLORS["GRAY"])
        # self.board = Board(305,125)
        self.players = [Player("SHAK"), Player("ALICE"), Player("NANCY"), Player("CLIFTON")]
        self.leaderboard.players = self.players
        self.top_bar = TopBar(10, 10, self.WIDTH * 0.95, self.HEIGHT * 0.1)
        self.top_bar.change_round(1)
        self.bottom_bar = BottomBar(self.WIDTH * 10 / 800, self.HEIGHT * 475 / 600, self)
        self.chat = Chat(self.WIDTH * 670 / 800, self.HEIGHT * 100 / 600, self)
        # self.backgroundTiles = pygame.sprite.Group()
        # self.helpbox = thorpy.Box(elements=[thorpy.Element("Hello")])
        self.myrack = Inventory(self.WIDTH * 245 / 800, self.HEIGHT * 485 / 600, 75, 2, 4, COLORS["ORANGE"])
        self.extrarack = Inventory(self.WIDTH * 125 / 800, self.HEIGHT * 485 / 600, 75, 2, 2, COLORS["RED"])

        self.tileList = pygame.sprite.Group()
        self.bag = pygame.sprite.Group()

    def draw(self):
        self.win.fill(self.BGCOLOR)
        self.leaderboard.draw(self.win)
        self.top_bar.draw(self.win)
        self.bottom_bar.draw(self.win)
        # self.middle_bar.draw(self.win)
        self.inventory.draw(self.win)
        self.myrack.draw(self.win)
        self.extrarack.draw(self.win)
        self.chat.draw(self.win)
        for tile in self.tileList:
            tile.inBox(self.inventory)
            if tile.inabox:
                tile.image = pygame.transform.scale(tile.original, (75, 75))
                tile.size = tile.image.get_size()
                # print("in box")
            else:
                tile.image = pygame.transform.scale(tile.original, (75, 75))
                tile.size = tile.image.get_size()
                # print("not in box")
        self.tileList.draw(self.win)
        self.bag.draw(self.win)
        self.inventory.tilegroup.draw(self.win)
        pygame.display.update()

    def check_clicks(self):
        """
        handles clicks on buttons and screen
        :return: None
        """
        pos = pygame.mouse.get_pos()
        # print(pos)
        x, y = pos
        # move tiles
        for tile in self.tileList:
            if tile.rect.collidepoint(pos):
                tile.clicked = True
                return tile
                break

    def main(self):
        global FPSCLOCK, DISPLAYSURF
        pygame.init()
        pygame.display.set_caption('beta version BuyGame')

        # self.box = thorpy.Box(elements=[slider,button1])
        #
        # #we regroup all elements on a menu, even if we do not launch the menu
        # menu = thorpy.Menu(self.box)
        # #important : set the screen as surface for all elements
        # for element in menu.get_population():
        #     element.surface = self.win
        # self.box.set_topleft((100,100))

        self.bag.add(Bag(self.WIDTH * 0.05, self.HEIGHT * 0.72))
        FPSCLOCK = pygame.time.Clock()
        # screen = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        mousex = 0  # used to store x coordinate of mouse event
        mousey = 0  # used to store y coordinate of mouse event
        # letter = 'C'
        FONT = pygame.font.SysFont('comicsans', 100)

        while True:  # main game loop
            if self.tileID % 2:
                letter = 'A'
            else:
                letter = 'B'
            mouseClicked = False
            for event in pygame.event.get():  # event handling loop
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    x, y = pos
                    selected = self.check_clicks()
                    self.bottom_bar.button_events()
                    if event.button == 1:
                        boxpos = self.inventory.Get_pos()
                        if self.inventory.In_grid(boxpos[0], boxpos[1]):
                            print("in grid")
                            print(self.inventory.items)
                    if event.button == 3:
                        self.tileList.add(Tile(x, y, self.tileID, letter, 1))
                        self.tileID += 1
                if event.type == pygame.MOUSEBUTTONUP:
                    boxpos = self.inventory.Get_pos()
                    for tile in self.tileList:
                        tile.clicked = False
                    if selected and self.inventory.In_grid(boxpos[0], boxpos[1]):
                        self.inventory.Add(selected, boxpos)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.chat.update_chat()
                    else:
                        # gets the key name
                        key_name = pygame.key.name(event.key)
                        # converts to uppercase the key name
                        key_name = key_name.lower()
                        self.chat.type(key_name)
                # menu.react(event)
            for tile in self.tileList:
                if tile.clicked:
                    # center tile on mouse and move around
                    pos = pygame.mouse.get_pos()
                    tile.rect.x = pos[0] - (tile.rect.width / 2.4)
                    tile.rect.y = pos[1] - (tile.rect.height / 2.4)
                    break  # prevents more than one tile at a time
            # box.blit()
            # box.update()
            self.draw()


class Tile(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, id, letter='C', score=None):
        super(Tile, self).__init__()
        self.id = id
        self.original = pygame.image.load(os.path.join("Tiles", f"{letter}.png"))
        self.image = pygame.image.load(os.path.join("Tiles", f"{letter}.png"))
        self.size = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.size = self.image.get_size()
        self.clicked = False
        self.rect = self.image.get_rect()
        self.rect.y = ypos - self.rect.height / 2
        self.rect.x = xpos - self.rect.height / 2
        self.score = score
        self.letter = letter
        self.inabox = False

    def inBox(self, inventory):
        box_size = 75
        border = 3
        # print(f"Tile Position is {self.rect.x} and {self.rect.y}")
        x = self.rect.left - inventory.x
        y = self.rect.top - inventory.y
        x = x // (box_size + border)
        y = y // (box_size + border)
        # print(f"Tile Position is {x} and {y}")
        self.inabox = inventory.In_grid(x, y)
        return self.inabox


class Bag(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos):
        super(Bag, self).__init__()
        self.image = pygame.image.load(os.path.join("Tiles", "bag.jpg"))
        self.rect = self.image.get_rect()
        self.rect.y = ypos - self.rect.height / 2
        self.rect.x = xpos - self.rect.height / 2
        self.count = 100


g = Game()
g.main()
