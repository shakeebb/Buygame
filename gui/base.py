import logging
import os

import pygame
import sys

from pygame.surface import Surface

import common
from common.client_utils import ClientUtils
from gui.bottom_bar import BottomBar
from gui.chat import Chat
from common import network
from common.game import *
from common.logger import log, Log, logger
from gui.display import Display
from gui.leaderboard import Leaderboard
from gui.snap import Inventory
from gui.top_bar import TopBar
from common.gameconstants import *


class GameUI:
    def __init__(self, name: str):
        Display.init()
        self.tileID = 0
        self.surface = Display.surface()

        self.top_bar = TopBar(0.5, 0.5, Display.num_horiz_cells() - 1, 4)
        self.leaderboard = Leaderboard(0.5, self.top_bar.ymargin() + 1, 5, 10)
        self.chat = Chat(Display.num_horiz_cells() - 10, self.top_bar.ymargin() + 0.5,
                         10, Display.num_vert_cells() - 6,
                         self)
        # self.board = Board(305,125)
        self.inventory = Inventory(self.leaderboard.xmargin() + 5,
                                   self.top_bar.ymargin() + 4,
                                   self.chat.h_margin_cells - 2,
                                   2, 2.5, 1, 10, Colors.GRAY.value)
        # self.inventory = Inventory((self.chat.h_margin_cells - self.leaderboard.xmargin()) / 2,
        #                            self.top_bar.ymargin() + 4,
        #                            24, 2.5, 75, 1, 10, Colors.GRAY.value)
        # self.inventory = Inventory(self.leaderboard.xmargin(), display_height * 300 / 600,
        # 75, 1, 10, Colors.GRAY.value)
        # self.inventory = Inventory(display_width * 0.08, display_height * 300 / 600, 75, 1, 10, Colors.GRAY.value)
        self.bag = Bag(self.leaderboard.xmargin() / 3, self.leaderboard.ymargin() + 1, 2)
        # self.chat = Chat(display_width * 670 / 800, display_height * 100 / 600, self)

        # self.backgroundTiles = pygame.sprite.Group()
        # self.helpbox = thorpy.Box(elements=[thorpy.Element("Hello")])
        self.bottom_bar = BottomBar(0.5, self.bag.ymargin() + 1,
                                    self.chat.h_margin_cells - 1,
                                    self.chat.ymargin() - self.bag.ymargin() - 1,
                                    self)

        self.myrack = Inventory(self.bottom_bar.h_margin_cells + 5,
                                self.bottom_bar.v_margin_cells + 1,
                                self.bottom_bar.v_margin_cells - 6, 2, 2.5, 1, 10, Colors.ORANGE.value)

        self.extrarack = Inventory(self.bottom_bar.h_margin_cells + 10,
                                   self.bottom_bar.v_margin_cells + 5,
                                   self.bottom_bar.v_margin_cells - 6, 2, 2.5, 1, 5, Colors.RED.value)

        # self.players = [PlayerGUI("SHAK"), PlayerGUI("ALICE"), PlayerGUI("NANCY"), PlayerGUI("CLIFTON"), PlayerGUI("SOUBHIK CHAKRABORTY")]
        # self.leaderboard.players = self.players
        self.top_bar.change_round(1)
        self.tileList = pygame.sprite.Group()
        self.network: network.Network = None
        self.player_name = name
        self.my_player_number = -1
        self.__game: Game = None
        path = os.path.dirname(__file__)
        self.tiles_sheet = SpriteSheet(os.path.join(path, "tiles", "all_tiles.png"))
        self.sprite_tiles: list[list[Surface]] = self.tiles_sheet.crop_out_sprites()
        self.game_status = GameStatus.INITIAL_STATE

    def draw(self):
        self.surface.fill(BG_COLOR)
        self.leaderboard.draw(self.surface)
        self.top_bar.draw(self.surface)
        # self.middle_bar.draw(self.win)
        self.inventory.draw(self.surface)
        self.chat.draw(self.surface)
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
        # self.bag.draw(self.surface)
        self.bag.drawMe()
        self.inventory.tilegroup.draw(self.surface)
        self.bottom_bar.draw(self.surface)
        self.myrack.draw(self.surface)
        self.extrarack.draw(self.surface)
        self.tileList.draw(self.surface)

        Display.display_grid()
        Display.show()

    def refresh_resolution(self, w, h):
        self.top_bar.refresh_dims()
        self.leaderboard.refresh_dims()
        self.inventory.refresh_dims()
        self.chat.refresh_dims()
        self.bag.refresh_dims()
        self.bottom_bar.refresh_dims()
        self.myrack.refresh_dims()
        self.extrarack.refresh_dims()
        pass

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
        pygame.display.set_caption('beta version BuyGame')
        # self.box = thorpy.Box(elements=[slider,button1])
        #
        # #we regroup all elements on a menu, even if we do not launch the menu
        # menu = thorpy.Menu(self.box)
        # #important : set the screen as surface for all elements
        # for element in menu.get_population():
        #     element.surface = self.win
        # self.box.set_topleft((100,100))

        # self.bag.add(Bag(w * 0.05, h * 0.72))
        FPSCLOCK = pygame.time.Clock()
        # screen = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        mousex = 0  # used to store x coordinate of mouse event
        mousey = 0  # used to store y coordinate of mouse event
        # letter = 'C'
        FONT = pygame.font.SysFont('comicsans', 100)
        logger.reset()
        try:
            self.network = network.Network()
            log("we connected to network - player no " + str(self.network.p))
            self.my_player_number = self.network.p
            self.network.send(ClientMsg.Name.msg + self.player_name)
            ret = self.network.send(ClientMsg.Get.msg)
            if ret is not None:
                self.set_game(ret)
                self.leaderboard.players = self.game().getPlayers()
                self.top_bar.gameui = self
            else:
                raise TypeError("Game object not received")
        except Exception as e:
            log(e)
            log("Couldn't connect")
            sys.exit("Cant connect to host")

        pygame.event.clear()
        while True:  # main game loop
            letter = chr(random.randint(65, 90))
            mouseClicked = False
            for event in pygame.event.get():  # event handling loop
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    pygame.quit()
                    self.network.disconnect()
                    sys.exit()
                if event.type == VIDEORESIZE:
                    log("About to video resize")
                    Display.resize(event, self.refresh_resolution)

                if event.type == EV_DICE_ROLL:
                    log("Received Roll dice event") if VERBOSE else None
                    self.bottom_bar.roll_dice()

                if event.type == EV_POST_START:
                    self.game_status = GameStatus.PLAY

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    x, y = pos
                    selected = self.check_clicks()
                    self.top_bar.button_events()
                    self.bottom_bar.button_events()
                    if event.button == 1:
                        boxpos = self.inventory.Get_pos()
                        if self.inventory.In_grid(boxpos[0], boxpos[1]):
                            log("in grid")
                            log(self.inventory.items)
                    if event.button == 3:
                        self.tileList.add(Tile(x, y, self.tileID, self.sprite_tiles, letter, 1))
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
            # %% end of event loop

            def sever_notify(msg: str, color: Colors = Colors.BLACK):
                self.top_bar.server_msg.set_text(msg)

            def client_notify(msg: str, color: Colors = Colors.BLACK):
                self.top_bar.client_msgs.add_msg(msg, color)

            if self.game_status == GameStatus.PLAY:
                self.game_status = ClientUtils.check_game_events(self.game(),
                                                                 self.my_player_number,
                                                                 self.network,
                                                                 sever_notify,
                                                                 client_notify)

            if self.game_status == GameStatus.ROLL_DICE:
                self.bottom_bar.enable_dice_rolling()

            if self.game_status == GameStatus.DICE_ROLL_COMPLETE:
                diceValue = str(self.bottom_bar.last_rolled_dice_no)
                diceMessage: str = ClientMsg.Dice.msg + diceValue
                try:
                    self.set_game(self.network.send(diceMessage))
                    self.game_status = GameStatus.PLAY
                except Exception as e:
                    log(e)

            def process_rack(rack: [common.game.Tile], temp=False):
                slot = 0
                for rT in rack:
                    inv = self.myrack if temp else self.inventory
                    _tile = Tile(inv.x, inv.y, self.tileID, self.sprite_tiles, rT.letter, 1)
                    xxx = inv.items[0]
                    print(xxx)
                    if slot < len(inv.items[0]):
                        inv.Add(_tile, (0, slot))
                    slot += 1
                    # if not temp:
                    #     self.myrack.tilegroup.add(_tile)
                    # else:
                    #     self.inventory.tilegroup.add(_tile)

            if self.game_status == GameStatus.RECEIVE_RACKS:
                try:
                    player = self.game().getPlayer(self.my_player_number)
                    self.game_status = ClientUtils.receivedRacks(player, self.network, self.my_player_number,
                                                                 sever_notify, client_notify,
                                                                 process_rack)
                    # ?? self.set_game(network.send("Done"))
                except Exception as e:
                    log(e)

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

    def set_game(self, _g: object):
        assert isinstance(_g, Game)
        self.__game = _g
        self.top_bar.server_msg.set_text(self.__game.getServerMessage())

    def game(self) -> Game:
        return self.__game


class SpriteSheet:
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error:
            print("Unable to load: %s " % filename)
            raise SystemExit

    def crop_out_sprites(self, width: int = 128, height: int = 128):
        all_sprites = [[pygame.Surface([width, height]) for _ in range(5)] for _ in range(6)]
        for j in range(0, 6):
            for i in range(0, 5):
                surf = all_sprites[j][i]
                surf.blit(self.sheet, (0,0), (i*width, j*height, width, height))
                pygame.draw.rect(surf, Colors.BLACK.value, (0, 0, width-1, height-1), 1)
        if VERBOSE:
            for x in all_sprites:
                for y in x:
                    print(y.get_size())
        return all_sprites


class Tile(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, id, tile_sprites: list[list[Surface]], letter='C', score=None):
        super(Tile, self).__init__()
        self.id = id
        self.all_tiles = tile_sprites
        # self.original = pygame.image.load(os.path.join("tiles", f"{letter}.png"))
        if "WILD" in letter:
            row = 5
            col = 3
        else:
            row = int((ord(letter)-65) / 5)
            col = int((ord(letter)-65) % 5)
        self.image = self.all_tiles[row][col]
        self.original = self.image
        # self.image = pygame.image.load(os.path.join("tiles", f"{letter}.png"))
        self.size = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.size = self.image.get_size()
        self.clicked = False
        self.rect = self.image.get_rect()
        self.update_rect(xpos, ypos)
        self.score = score
        self.letter = letter
        self.inabox = False
        self.init = True

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

    def update_rect(self, xpos, ypos):
        self.rect.x = xpos - self.rect.width / 2
        self.rect.y = ypos - self.rect.height / 2
        __r = self.original.get_rect()
        __r.x = self.rect.x
        __r.y = self.rect.y


class Bag(Display):
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
        if VERBOSE:
            print("Box %s " % self.box_size)


if __name__ == "__main__":
    g = GameUI("Test")
    g.main()
