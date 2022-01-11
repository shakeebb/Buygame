import logging
import os
import time
from threading import Thread, Event

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
from gui.label import MessageList
from gui.leaderboard import Leaderboard
from gui.main_menu import MainMenu
from gui.snap import Inventory
from gui.top_bar import TopBar
from common.gameconstants import *


class GameUI:
    def __init__(self, main_menu: MainMenu):
        Display.init()
        self.main_menu = main_menu
        self.server_settings = self.main_menu.game_settings['server_defaults']
        usr_defs = self.main_menu.game_settings['user_defaults']

        self.player_name = self.main_menu.controls[0].text
        input_ip = self.main_menu.controls[1].text
        self.ip = input_ip if len(input_ip) > 0 else self.server_settings['ip']
        self.port = self.server_settings['port']

        if self.player_name not in dict(usr_defs):
            usr_defs[self.player_name] = {}
        self.user_settings = usr_defs[self.player_name]

        self.my_player_number = -1
        if 'session_id' in self.user_settings:
            self.session_id = self.user_settings['session_id']
        else:
            self.session_id = ""

        self.surface = Display.surface()

        self.top_bar = TopBar(0.5, 0.5, Display.num_horiz_cells() - 1, 4)
        self.leaderboard = Leaderboard(0.5, self.top_bar.ymargin() + 1, 5, 10)
        self.message_box = MessageList(Display.num_horiz_cells() - 10,
                                       self.top_bar.ymargin() + 0.5,
                                       10, 10,
                                       num_msgs=10, line_spacing=30, font_sz=18, bold_face=False,
                                       border_width=4, border_color=Colors.MAGENTA)
        # self.board = Board(305,125)
        self.temp_rack = Inventory(self.leaderboard.xmargin() + 11,
                                   self.top_bar.ymargin() + 1,
                                   self.message_box.h_margin_cells - 2,
                                   2, 2.5, 1, 5, display_dollar_value=True,
                                   border_color=Colors.LT_GRAY, box_color=Colors.WHITE)

        self.inventory = Inventory(self.leaderboard.xmargin() + 5,
                                   self.top_bar.ymargin() + 5,
                                   self.message_box.h_margin_cells - 2,
                                   2, 2.5, 1, 10, display_dollar_value=True,
                                   border_color=Colors.GRAY)
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
                                    Display.num_horiz_cells() - 11,
                                    Display.num_vert_cells() - self.bag.ymargin() - 1,
                                    # self.chat.ymargin() - self.bag.ymargin() - 1,
                                    self)

        self.chat = Chat(self.message_box.h_margin_cells, self.bottom_bar.v_margin_cells,
                         10, Display.num_vert_cells() - self.bottom_bar.v_margin_cells - 0.5,
                         self)

        self.myrack = Inventory(self.bottom_bar.h_margin_cells + 5,
                                self.bottom_bar.v_margin_cells + 1,
                                self.bottom_bar.v_margin_cells - 6, 2, 2.5, 1, 13, border_color=Colors.GRAY)

        self.extrarack = Inventory(self.bottom_bar.h_margin_cells + 15,
                                   self.bottom_bar.v_margin_cells + 5,
                                   self.bottom_bar.v_margin_cells - 6, 2, 2.5, 1, 5, border_color=Colors.GRAY)

        self.top_bar.change_round(1)
        self.tileList = pygame.sprite.Group()
        self.network: network.Network = None
        self.__game: Game = None
        path = os.path.dirname(__file__)
        self.tiles_sheet = SpriteSheet(os.path.join(path, "tiles", "all_tiles.png"))
        self.sprite_tiles: list[list[Surface]] = self.tiles_sheet.crop_out_sprites()
        self.game_status = GameUIStatus.INITIAL_STATE
        self.hb_thread = Thread(target=self.heartbeat, name="heartbeat", daemon=True)
        self.hb_event = Event()
        self.last_notification_received = 0
        self.current_round = -1

    def quit(self):
        self.main_menu.save_gamesettings()
        self.hb_event.set()
        self.hb_thread.join()

    def draw(self):
        self.surface.fill(BG_COLOR)
        self.leaderboard.draw(self.surface)
        self.top_bar.draw(self.surface)
        # self.middle_bar.draw(self.win)
        self.message_box.draw(self.surface)
        # for tile in self.tileList:
        #     tile.inBox(self.inventory)
        #     if tile.inabox:
        #         tile.image = pygame.transform.scale(tile.original, (75, 75))
        #         tile.size = tile.image.get_size()
        #         # print("in box")
        #     else:
        #         tile.image = pygame.transform.scale(tile.original, (75, 75))
        #         tile.size = tile.image.get_size()
        #         # print("not in box")
        # self.bag.draw(self.surface)
        self.bag.drawMe()
        self.bottom_bar.draw(self.surface)
        self.chat.draw(self.surface)

        self.temp_rack.draw(self.surface)
        self.inventory.draw(self.surface)
        self.myrack.draw(self.surface)
        self.extrarack.draw(self.surface)

        def tile_grp(_inv: Inventory):
            _inv.tile_group.draw(self.surface)

        for __i in [self.inventory, self.myrack, self.extrarack, self.temp_rack]:
            tile_grp(__i)
        # self.tileList.draw(self.surface)

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

        def check_tiles(tiles):
            # move tiles
            for tile in tiles:
                if tile.rect.collidepoint(*pos):
                    tile.clicked = True
                    return tile
            return None

        # ret_val = check_tiles(self.tileList)
        # if ret_val is not None:
        #     log(f"tilelist: mouse down on {ret_val}")
        #     return ret_val

        ret_val = check_tiles(self.inventory.tile_group)
        if ret_val is not None:
            # log(f"inventory: mouse down on {ret_val}")
            return ret_val

        ret_val = check_tiles(self.myrack.tile_group)
        if ret_val is not None:
            # log(f"myrack: mouse down on {ret_val}")
            return ret_val

        ret_val = check_tiles(self.extrarack.tile_group)
        if ret_val is not None:
            # log(f"extrarack: mouse down on {ret_val}")
            return ret_val

        return None

    def heartbeat(self):
        while not self.hb_event.is_set():
            try:
                player: Player = self.me()
                # if player.player_state == PlayerState.WAIT or player.player_state == PlayerState.INIT:
                if True:
                    ret_game = self.network.send(ClientMsgReq.Get.msg +
                                                 "notifications_received=" +
                                                 str(self.last_notification_received)
                                                 )
                    if ret_game is None:
                        continue
                    assert isinstance(ret_game, Game)
                    self.set_game(ret_game)
                    # myself = self.me()
                    # if myself.player_state == PlayerState.PLAY:
                    #     if ret_game.game_state == GameState.ROLL:
                    #         self.game_status = GameUIStatus.ROLL_DICE
                    #     elif ret_game.game_state == GameState.BUY:
                    #         self.game_status = GameUIStatus.ENABLE_BUY
                    #     elif ret_game.game_state == GameState.SELL:
                    #         self.game_status = GameUIStatus.ENABLE_SELL
                    #     # self.messagebox_notify(ret_game.get_server_message())
                    #     self.top_bar.set_connection_status(Colors.GREEN)
                    # elif myself.player_state == PlayerState.WAIT:
                    #     self.top_bar.set_connection_status(Colors.YELLOW)
                # elif self.game_status == GameUIStatus.WAIT_TURN:
                #     ret_game = self.network.send(ClientMsgReq.Get.msg +
                #                                  "notifications_received=" +
                #                                  str(self.last_notification_received)
                #                                  )
                #     if ret_game is None:
                #         continue
                #     assert isinstance(ret_game, Game)
                #     self.set_game(ret_game)
                # elif self.game_status == GameUIStatus.WAIT_ALL_PLAYED:
                #     self.check_round_complete()
                # else:
                #     self.network.heartbeat()
            finally:
                self.hb_event.wait(WAIT_POLL_INTERVAL)

    def main(self):
        pygame.display.set_caption('beta version BuyGame')
        logger.reset()

        self.handshake()

        pygame.event.clear()
        selected = None
        self.hb_thread.start()

        while True:  # main game loop
            letter = chr(random.randint(65, 90))
            mouseClicked = False
            for event in pygame.event.get():  # event handling loop
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    self.quit()
                    pygame.quit()
                    sys.exit()
                if event.type == VIDEORESIZE:
                    log("About to video resize")
                    Display.resize(event, self.refresh_resolution)

                if event.type == EV_DICE_ROLL:
                    log("Received Roll dice event") if VERBOSE else None
                    self.bottom_bar.roll_dice()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    x, y = pos
                    selected = self.check_clicks()
                    self.top_bar.button_events()
                    self.bottom_bar.button_events()
                    # if event.button == 1:
                    #     boxpos = self.inventory.Get_pos()
                    #     if self.inventory.In_grid(boxpos[0], boxpos[1]):
                    #         log("mousedown: in inventory grid")
                    #         # log(self.inventory.items)
                    #
                    #     boxpos = self.myrack.Get_pos()
                    #     if self.myrack.In_grid(boxpos[0], boxpos[1]):
                    #         log("mousedown: in myrack grid")
                    #         # log(self.myrack.items)
                    # if event.button == 3:
                    #     self.tileList.add(Tile(x, y, self.tileID, self.sprite_tiles, letter, 1))
                    #     self.tileID += 1

                if event.type == pygame.MOUSEBUTTONUP:
                    def button_up(_inv: Inventory):
                        try:
                            _boxpos = _inv.Get_pos()
                            if selected and _inv.In_grid(_boxpos[0], _boxpos[1]):
                                self.inventory.remove_tile(selected)
                                self.myrack.remove_tile(selected)
                                self.extrarack.remove_tile(selected)
                                _inv.Add(selected, _boxpos)
                                return True
                        finally:
                            for tile in _inv.tile_group:
                                tile.clicked = False
                            self.top_bar.word = self.inventory.get_word()

                    for __i in [self.inventory, self.myrack, self.extrarack]:
                        if button_up(__i):
                            break
                    selected = None

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

            # ---------------------------
            # %% end of event loop
            # ---------------------------
            self.handle_gaming_events()

            def update_tile_pos(tiles):
                for __tile in tiles:
                    if __tile.clicked:
                        # center tile on mouse and move around
                        pos = pygame.mouse.get_pos()
                        __tile.rect.x = pos[0] - (__tile.rect.width / 2.4)
                        __tile.rect.y = pos[1] - (__tile.rect.height / 2.4)
                        return True  # prevents more than one tile at a time
                return False

            if update_tile_pos(self.tileList):
                pass
            elif update_tile_pos(self.inventory.tile_group):
                pass
            elif update_tile_pos(self.myrack.tile_group):
                pass

            # box.blit()
            # box.update()
            self.draw()

    def refresh_inventory(self, clear_inventory=False):
        try:
            self.leaderboard.players = self.game().players()
            player = self.me()
            self.myrack.clear()
            self.temp_rack.clear()
            self.extrarack.clear()
            if clear_inventory:
                self.inventory.clear()
                self.top_bar.word = self.inventory.get_word()

            def process_rack(rack: [common.game.Tile], temp=False):
                for rT in rack:
                    if rT is None:
                        self.client_notify("Received empty letters in the rack")
                        continue
                    # skip the inventory letters moved by the user
                    if self.inventory.contains_letter(rT.letter):
                        continue

                    inv = self.temp_rack if temp else self.myrack
                    import gui
                    _tile = gui.base.Tile(inv.x, inv.y, rT.get_tile_id(), self.sprite_tiles, rT.get_letter(),
                                          inv.box_size, rT.score)
                    if rT.letter == WILD_CARD:
                        self.extrarack.Add(_tile)
                    else:
                        inv.Add(_tile)

            # %% end of process_rack

            ClientUtils.receive_racks(player, self.game_status, self.my_player_number,
                                      self.server_notify,
                                      self.client_notify,
                                      self.messagebox_notify,
                                      process_rack)

        except Exception as e:
            log("refresh inventory failed", e)

    def server_notify(self, msg: str, color: Colors = Colors.BLACK):
        self.top_bar.server_msg.set_text(msg)

    def client_notify(self, msg: str, color: Colors = Colors.BLACK):
        self.top_bar.client_msgs.add_msg(msg, color)

    def process_server_notifications(self):
        last_notification: Notification = None
        for n in self.me().notify_msg:
            if n.n_id <= self.last_notification_received:
                continue
            # log(f"SB: adding notify {n.get_msg()}")
            self.messagebox_notify(n.get_msg())
            last_notification = n

        if last_notification is not None:
            self.last_notification_received = last_notification.n_id

    def messagebox_notify(self, msg: str, color: Colors = Colors.BLACK):
        self.message_box.add_msg(msg, color)

    def check_round_complete(self):
        (self.game_status, r, _g_obj) = ClientUtils.round_done(self.top_bar.round, self.network,
                                                               self.client_notify,
                                                               self.messagebox_notify)
        self.set_game(_g_obj)
        self.top_bar.change_round(r)

    def set_game(self, _g: object):
        assert isinstance(_g, Game)
        self.__game = _g
        self.leaderboard.players = self.__game.players()
        self.top_bar.server_msg.set_text(self.__game.get_server_message())
        self.process_server_notifications()
        if self.current_round < self.__game.round:
            # assert self.game_status == GameUIStatus.I_PLAYED or self.game_status == GameUIStatus.INITIAL_STATE\
            #     or self.game_status == GameUIStatus.WAIT_START,\
            #     f"{self.game_status}"
            self.mark_round_complete()

    def mark_round_complete(self):
        if self.current_round != -1:
            self.top_bar.client_msgs.add_msg(f"UI: moving from round {self.current_round} to {self.__game.round}")
        self.current_round = self.__game.round
        self.game_status = GameUIStatus.PLAY
        self.top_bar.set_connection_status(Colors.GREEN)
        self.top_bar.round = self.current_round
        self.bottom_bar.hide_all()
        self.refresh_inventory(True)

    def game(self) -> Game:
        return self.__game

    def check_sell_again(self):
        if self.game_status == GameUIStatus.SELL_AGAIN:
            self.bottom_bar.enable_sell()
            self.game_status = GameUIStatus.ENABLE_SELL
            remaining = self.me().get_remaining_letters()
            self.messagebox_notify(f"Sell atleast {remaining} letter(s).", Colors.RED)
            self.refresh_inventory(True)
        elif self.game_status == GameUIStatus.SOLD:
            self.game_status = GameUIStatus.I_PLAYED
        elif self.game_status == GameUIStatus.SELL_FAILED:
            self.game_status = GameUIStatus.I_PLAYED

    def handshake(self):
        try:
            self.network = network.Network(self.ip, self.port, self.session_id, self.player_name)
            game = self.network.connect()
            log("we connected to network - session id: " + self.network.session_id)
            self.set_game(game)
            new_session_id = self.network.session_id

            def extract_player_id():
                return new_session_id.split('-')[2].split('=')[1][:-1]

            self.my_player_number = int(extract_player_id())
            user_defs = self.user_settings
            user_defs['player_id'] = self.my_player_number
            user_defs['name'] = self.player_name
            user_defs['session_id'] = new_session_id
            self.server_settings['ip'] = self.main_menu.controls[1].text
            self.main_menu.save_gamesettings()

            if game is None:
                ret = self.network.send(ClientMsgReq.Get.msg +
                                        "notifications_received=" +
                                        str(0)  # initially receive everything
                                        )
                if ret is not None:
                    game = ret
                else:
                    raise TypeError("Game object not received")
            self.set_game(game)
            self.leaderboard.players = self.game().players()
            self.top_bar.gameui = self
            cs = self.me().player_state
            if cs == PlayerState.WAIT or cs == PlayerState.INIT:
                self.game_status = GameUIStatus.WAIT_START
                # self.messagebox_notify(game.get_server_message())
                self.top_bar.set_connection_status(Colors.YELLOW)
            else:
                self.game_status = GameUIStatus.PLAY
                self.top_bar.set_connection_status(Colors.GREEN)
            for n in self.me().notify_msg:
                self.messagebox_notify(n.get_msg())
            self.refresh_inventory()
        except Exception as e:
            log("gui initialization failed with ", e)
            log("Couldn't connect")
            sys.exit("Cant connect to host")

    def me(self) -> Player:
        return self.game().players()[self.my_player_number]

    def handle_gaming_events(self):
        current_state = self.me().player_state
        if current_state == PlayerState.WAIT or current_state == PlayerState.INIT:
            return

        assert current_state == PlayerState.PLAY

        game_state = self.game().game_state

        if game_state == GameState.ROLL:
            if self.game_status.value < GameUIStatus.ROLL_DICE.value:
                self.game_status = GameUIStatus.ROLL_DICE
                self.bottom_bar.enable_dice_rolling()
                return

            if self.game_status == GameUIStatus.DICE_ROLL_COMPLETE:
                assert self.game_status == GameUIStatus.DICE_ROLL_COMPLETE, f"{self.game_status}"
                diceValue = str(self.bottom_bar.last_rolled_dice_no)
                diceMessage: str = ClientMsgReq.Dice.msg + diceValue
                try:
                    self.set_game(self.network.send(diceMessage))
                except Exception as e:
                    log("dice roll notify failed", e)

            self.refresh_inventory()
            # %% end of server side DICE_ROLL handling
            return

        elif game_state == GameState.BUY:
            if self.game_status.value < GameUIStatus.ENABLE_BUY.value:
                self.bottom_bar.enable_buy()
                self.refresh_inventory()
                self.game_status = GameUIStatus.BUY_ENABLED
                return
            elif self.game_status == GameUIStatus.BUY_ENABLED:
                return

            self.refresh_inventory()
            if self.game_status == GameUIStatus.BUY:
                try:
                    (self.game_status, _g_obj) = ClientUtils.buy_tiles(self.game(), self.network,
                                                                       self.my_player_number,
                                                                       self.server_notify,
                                                                       self.client_notify,
                                                                       self.messagebox_notify)
                    self.set_game(_g_obj)
                except Exception as e:
                    log("buy failed", e)

            elif self.game_status == GameUIStatus.CANCEL_BUY:
                (self.game_status, _g_obj) = ClientUtils.cancel_buy(self.game(), self.network,
                                                                    self.server_notify,
                                                                    self.client_notify)
                self.set_game(_g_obj)
            else:
                self.bottom_bar.hide_all()

            self.refresh_inventory()
            # %% end of server side BUY handling
            return

        elif game_state == GameState.SELL:
            if self.game_status.value < GameUIStatus.ENABLE_SELL.value:
                self.bottom_bar.enable_sell()
                self.refresh_inventory(True)
                self.game_status = GameUIStatus.SELL_ENABLED
                return
            elif self.game_status == GameUIStatus.SELL_ENABLED:
                return

            if self.game_status == GameUIStatus.SELL:
                if len(self.top_bar.word) == 0:
                    self.messagebox_notify("Cannot sell a blank word", Colors.RED)
                    self.game_status = GameUIStatus.ENABLE_SELL
                    return
                try:
                    (self.game_status, _g_obj) = ClientUtils.sell_word(self.game(), self.network,
                                                                       self.my_player_number,
                                                                       self.top_bar.word,
                                                                       self.server_notify,
                                                                       self.client_notify,
                                                                       self.messagebox_notify)
                    self.set_game(_g_obj)
                except Exception as e:
                    log("sell word failed", e)

            elif self.game_status == GameUIStatus.CANCEL_SELL:
                (g_status, _g_obj) = ClientUtils.cancel_sell(self.network, self.server_notify, self.client_notify)
                if g_status is not None:
                    self.game_status = g_status
                    self.set_game(_g_obj)

            self.check_sell_again()
            # %% end of server side SELL handling
            return

        """
        if self.game_status == GameStatus.PLAY or self.game_status == GameStatus.WAIT_TURN:
            self.game_status = ClientUtils.check_game_events(self.game(),
                                                             self.my_player_number,
                                                             self.game_status,
                                                             self.server_notify,
                                                             self.messagebox_notify)

        if self.game_status == GameStatus.RECEIVE_RACKS:
            self.refresh_inventory()
            self.game_status = GameStatus.ENABLE_BUY

        if self.game_status == GameUIStatus.ENABLE_SELL:
            self.bottom_bar.enable_sell()
            self.messagebox_notify("Create a word to sell")
            self.game_status = GameUIStatus.SELL_ENABLED

        if self.game_status == GameUIStatus.I_PLAYED:
            (self.game_status, _g_obj) = ClientUtils.i_played(self.top_bar.round, self.network)
            self.set_game(_g_obj)

        if self.game_status == GameUIStatus.TURN_COMPLETE:
            self.check_round_complete()
        """


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


class Tile(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, id, tile_sprites: list[list[Surface]], letter='C',
                 box_size: int = 50,
                 score=None):
        super(Tile, self).__init__()
        self.id = id
        self.all_tiles = tile_sprites
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
        self.image = pygame.transform.scale(self.image, (int(box_size), int(box_size)))
        self.size = self.image.get_size()
        self.box_size = box_size
        self.clicked = False
        self.rect = self.image.get_rect()
        self.update_rect(xpos, ypos)
        self.score = score
        self.letter: str = letter
        self.inabox = False
        self.init = True
        self._layer = 4

    def __str__(self):
        return type(self).__name__ + " " + self.letter

    def inBox(self, inventory):
        border = 3
        # print(f"Tile Position is {self.rect.x} and {self.rect.y}")
        x = self.rect.left - inventory.x
        y = self.rect.top - inventory.y
        x = x // (self.box_size + border)
        y = y // (self.box_size + border)
        # print(f"Tile Position is {x} and {y}")
        self.inabox = inventory.In_grid(x, y)
        return self.inabox

    def update_rect(self, xpos, ypos):
        # self.rect.x = xpos - self.rect.width / 2
        # self.rect.y = ypos - self.rect.height / 2
        self.rect.x = xpos
        self.rect.y = ypos
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
    if len(sys.argv) == 0:
        log("Provide user name as the first argument")
        sys.exit(1)
    mm = MainMenu(False, False)
    mm.controls[0].text = sys.argv[1]
    gui = GameUI(mm)
    gui.main()
