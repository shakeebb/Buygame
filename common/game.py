# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 11:44:56 2021

@author: Boss
"""
import csv
import inspect
import os.path
import random
from collections import deque
from datetime import datetime
from enum import Enum, auto
from random import shuffle
from threading import RLock

from common.gameconstants import WILD_CARD, MAX_LETTERS_ON_HOLD
from common.logger import log
from common.utils import write_file

nofw = 4
# import player as pl
# defining game dice
dice = ['2', '3', '4', '5', 'Your Choice', 'Your Choice']
# will store values of user
myTiles = []


class PlayerState(Enum):
    INIT = auto()
    PLAY = auto()
    WAIT = auto()

    def __repr__(self):
        return self.name


class NotificationType(Enum):
    INFO = auto()
    WARN = auto()
    ERR = auto()
    ACT_1 = auto()
    ACT_2 = auto()

    def __repr__(self):
        return self.name


class Notification:
    def __init__(self, n_id: int, n_type: NotificationType, msg: str):
        self.n_id = n_id
        self.n_type = n_type
        self.n_msg = msg

    def __repr__(self):
        return f"{self.n_id} - {self.n_msg}"

    def get_msg(self):
        return '- ' + self.n_msg

    def get_notify_type(self):
        return self.n_type


# df representing bag with tiles and their values and amounts
def word_value(sold_word):
    score = 0
    for tile in sold_word:
        score += tile.score
    return score ** 2


class Txn(Enum):
    INIT = auto()
    BOUGHT = auto()
    BUY_CANCELLED = auto()
    SOLD = auto()
    SOLD_SELL_AGAIN = auto()
    SELL_CANCELLED = auto()
    SELL_CANCELLED_SELL_AGAIN = auto()
    BUY_FAILED = auto()
    BUY_CANCEL_FAILED = auto()
    SELL_FAILED = auto()
    SELL_CANCEL_FAILED = auto()


class Player:
    """

    Creates an instance of a player.
    Initializes the player's rack, and allows you
    to set/get a player name """

    def __init__(self, game, nofw, num, name, team, bag):
        # Intializes a player instance. Creates the player's rack by creating an instance of that class.
        # Takes the bag as an argument, in order to create the rack.
        self.game = game
        self.number = num
        self.name = name
        self.active = False
        self.rack = Rack(nofw, bag)
        self.money = 200
        self.team = team
        self.txn_status = Txn.INIT
        self.wordvalue = 0
        self.message = ""
        self.played = False
        self.start = False
        self.notify_msg: deque[Notification] = deque([], 20)
        self.player_state = PlayerState.WAIT
        self.notification_id = 0
        self.session_id = ""

    def __repr__(self):
        return f"{self.name}-{self.number}-{self.player_state}-{self.active}"

    def set_name(self, name):
        # Sets the player's name.
        self.name = name

    def set_state(self, s):
        self.player_state = s

    def set_notify(self, n_type: NotificationType, msg: str):
        self.notify_msg.append(Notification(self.notification_id, n_type, msg))
        self.notification_id += 1

    def set_start(self):
        # Sets the player's name.
        self.start = True

    def get_name(self):
        # Gets the player's name.
        return self.name

    def set_active(self):
        self.active = True

    def set_inactive(self):
        self.active = False

    def insufficient_balance(self):
        self.player_state = PlayerState.WAIT
        msg = f"${self.money} not enough to buy for ${self.rack.get_temp_value()}"
        self.set_notify(NotificationType.WARN,
                        msg)
        self.game.track(self, lambda gte: gte.update_msg(msg, NotificationType.WARN))
        self.rack.clear_temp_rack()

    # def setPlayerMessage(self, message):
    #     self.message = message
    #
    # def addPlayerMessage(self, message):
    #     self.message += message
    #
    def get_rack_str(self):
        # Returns the player's rack.
        return f"player {self.number} - {self.rack.get_rack_str()}"

    def get_temp_str(self):
        # Returns the player's rack.
        return f"player {self.number} temp - {self.rack.get_temp_str()}"

    def get_rack_arr(self):
        # Returns the player's rack in the form of an array.
        return self.rack.get_rack_arr()

    def get_rack_list(self):
        return self.rack.get_rack_list()

    # def increase_money(self, increase):
    #     # Increases the player's score by a certain amount. Takes the increase (int) as an argument and adds it to the score.
    #     self.money += increase

    # def get_money(self):
    #     # Returns the player's score
    #     return self.money

    def buy_word(self):
        cost = self.rack.get_temp_value()
        self.money -= cost
        self.rack.add_to_main()
        self.txn_status = Txn.BOUGHT
        self.game.player_bought(self, cost)
        return self

    def cancel_buy(self, bag):
        value = self.rack.rollback_rack(bag)
        self.txn_status = Txn.BUY_CANCELLED
        self.game.player_bought(self, value)

    def word_check(self, word):
        word = word.upper()
        racklist = self.get_rack_list()
        wildnumb = 0
        for w in word:
            if w not in racklist:
                if WILD_CARD not in racklist:
                    return False
                elif wildnumb > 0:
                    return False
                else:
                    racklist.remove(WILD_CARD)
                    wildnumb += 1
            else:
                racklist.remove(w)
        return True

    def word_remove(self, word):
        word = word.upper()
        for w in word:
            for tile in self.get_rack_arr():
                if tile.letter == w:
                    self.rack.remove_from_rack(tile)
                    break
        return self

    def _sell_word(self, word):
        word = word.upper()
        sell_word = []
        for w in word:
            if w in self.get_rack_list():
                for tile in self.get_rack_arr():
                    if w == tile.letter:
                        sell_word.append(tile)
                        self.rack.remove_from_rack(tile)
                        break
            else:
                for tile in self.get_rack_arr():
                    if WILD_CARD == tile.letter:
                        sell_word.append(tile)
                        self.rack.remove_from_rack(tile)
                        break
        return sell_word

    import pandas as pd

    def sell(self, word: str, word_dict: pd.DataFrame):
        # only 1 wild character is allowed in a single word.
        ret_val = None
        search_wrd = '^' + word.replace(WILD_CARD, ".", 1).lower() + '$'
        _found = word_dict[word_dict['words'].str.contains(search_wrd, regex=True).fillna(False)].count()
        if int(_found.values[0]) > 0:
            self.txn_status = self.word_check(word)
            if self.txn_status:
                sold_word = self._sell_word(word)
                value = int(word_value(sold_word))
                self.money += value
                self.txn_status = Txn.SOLD_SELL_AGAIN if self.get_remaining_letters() > 0 else Txn.SOLD
                ret_val = self.game.player_sold(self, sold_word, value)
        else:
            log(f"{word} (regex={search_wrd}) doesn't exists in the dictionary attempted by {self}")
            self.txn_status = False

        return ret_val

    def cancel_sell(self):
        if self.get_remaining_letters() > 0:
            self.txn_status = Txn.SELL_CANCELLED_SELL_AGAIN
            return

        self.txn_status = Txn.SELL_CANCELLED
        self.game.player_sold(self)

    def get_remaining_letters(self):
        return self.rack.num_non_wildcard_letters() - MAX_LETTERS_ON_HOLD


class GameState(Enum):
    INIT = auto()
    ROLL = auto()
    BUY = auto()
    SELL = auto()
    ROUND_COMPLETE = auto()
    END = auto()

    def __repr__(self):
        return self.name


class GameTrackerEntry:
    def __init__(self):
        self.game_id = ""
        self.game_state = GameState.INIT
        self.timestamp = ""
        self.session_id = ""
        self.player_name = ""
        self.player_state = PlayerState.INIT
        self.txn_status = Txn.INIT
        self.action = ""
        self.player_money = ""
        self.dice_rolled = 0
        self.buy_rack = ""
        self.sold_word = ""
        self.current_rack = ""
        self.letters_value = 0
        self.message_type = ""
        self.message = ""

    @classmethod
    def get_column_names(cls):
        return cls.__dict__.keys()

    def __repr__(self):
        return ','.join(self.__dict__.values())

    def _internal_dup_entry(self):
        entry = GameTrackerEntry()
        entry.update_game(self)
        # entry.game_id = self.game_id
        # entry.game_state = self.game_state
        return entry

    def update_game(self, g):
        self.game_id = g.game_id
        self.game_state = g.game_state

    def update_player(self, p: Player, value: int = 0):
        self.session_id = p.session_id
        self.player_name = p.name
        self.player_state = p.player_state
        self.txn_status = p.txn_status
        self.action = calling_func_name(3)
        self.player_money = p.money
        self.buy_rack = p.rack.get_temp_str()
        self.current_rack = p.rack.get_rack_str()
        if value > 0:
            self.letters_value = value

    def update_msg(self, msg: str, msg_type: NotificationType = NotificationType.INFO,
                   dice_rolled: int = 0, sold_word: str = "", value: int = 0):
        self.message_type = msg_type
        self.message = msg
        if dice_rolled > 0:
            self.dice_rolled = dice_rolled
        if len(sold_word) > 0:
            self.sold_word = sold_word
        if value > 0:
            self.letters_value = value
        self.timestamp = datetime.now().strftime("%m/%d/%Y %H.%M.%S")

    @classmethod
    def write_to_csv(cls, fp):
        csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC).writerow(
                GameTrackerEntry.get_column_names()
            )

    def commit(self, file):
        csv.writer(file, quoting=csv.QUOTE_NONNUMERIC).writerow(
                self.__dict__.values()
            )
        return self._internal_dup_entry()


def calling_func_name(level):
    return inspect.getouterframes(inspect.currentframe())[level].function


class Game:
    def __init__(self, g_id, game_tiles, server_path: str):
        self.game_id = g_id
        self._players: [Player] = []
        self.bag = Bag(game_tiles)
        self.turn = 0
        self.round = 0
        self.message = ""
        self.begin_time = datetime.now().strftime("%m/%d %H.%M.%S")
        self.game_state = GameState.INIT
        track_file = os.path.join(server_path, f"store/{g_id}.csv")
        write_file(track_file, GameTrackerEntry.write_to_csv)
        self.game_mutex = RLock()
        self.game_tracker = open(track_file, 'w', True)
        self.gte = GameTrackerEntry()

    def __repr__(self):
        return f"{self.game_id}-[{self.begin_time}]-{self.game_state}"

    def __getstate__(self):
        cur_state = self.__dict__.copy()
        # removing not picklable entry.
        del cur_state['game_mutex']
        del cur_state['game_tracker']
        return cur_state

    def __setstate__(self, new_state):
        self.__dict__.update(new_state)
        # NOTE: We don't want the game mutex on the client end.
        #       The client "always" asks the server for game object
        #       never "writes" back !!
        self.game_mutex = None
        self.game_tracker = None

    def players(self):
        return self._players

    def foreach_player(self, apply, condition=None, false_condition=None):
        for p in self._players:
            if condition is None or condition(p):
                apply(p)
            elif false_condition is not None:
                false_condition(p)

    def notify_waiting_players(self, msg):
        self.foreach_player(lambda _p: _p.set_notify(NotificationType.ACT_1, msg),
                            lambda _p: _p.player_state == PlayerState.WAIT)

    def notify_all_players(self, p_number, self_msg, other_msg):
        self.foreach_player(lambda _p: _p.set_notify(NotificationType.ACT_1, other_msg),
                            lambda _p: _p.number != p_number,
                            lambda _p: _p.set_notify(NotificationType.ACT_2, self_msg))

    def set_roll(self):
        if self.round > 15:
            self.game_state = GameState.END
            return
        self.game_state = GameState.ROLL
        self.round += 1
        if self.turn == len(self._players) - 1:
            self.turn = 0
        else:
            self.turn += 1
        p = self._players[self.turn]
        p.set_state(PlayerState.PLAY)
        self.foreach_player(lambda _o: _o.set_state(PlayerState.WAIT),
                            lambda _o: _o.number != p.number)

        s_msg = f"You need to roll the dice"
        o_msg = f"{p.name} needs to roll the dice"
        self.notify_all_players(p.number, s_msg, o_msg)
        self.track(p, lambda gte: gte.update_msg(o_msg))

    def track(self, p: Player, cb):
        self.gte.update_game(self)
        self.gte.update_player(p)
        cb(self.gte)
        self.gte = self.gte.commit(self.game_tracker)

    def players_in_state(self, s) -> list:
        return list(filter(lambda p: p.player_state == s, self._players))

    def player_rolled(self, p: Player, dice_value: int):
        n = len(self.players())
        if self.bag.get_remaining_tiles() < (
                dice_value * n):
            err_msg = f"cannot draw {dice_value} out of {self.bag.get_remaining_tiles()} letters."
            log(f"insufficient {dice_value} letters for {n} players in bag."
                f"remaining={self.bag.get_remaining_tiles()}")
            self.foreach_player(lambda _p: _p.set_notify(NotificationType.ERR, err_msg))
            self.game_state = GameState.END
            self.track(p, lambda gte: gte.update_msg(err_msg, NotificationType.ERR))
            return self.game_state

        self.track(p, lambda gte: gte.update_msg(f"{p.name} rolled dice to {dice_value}",
                                                 dice_rolled=dice_value))
        # %% we have enough, are racks initialized?
        # giving racks their bag and dice values
        try:
            self.foreach_player(lambda _p: _p.rack.clear_temp_rack())
        except Exception as e:
            log(f"{self} clear rack failed: ", e)

        self.foreach_player(lambda _p: _p.rack.add_to_rack(dice_value, self.bag))

        log(f"{self} handed racks to all")

        def log_racks(_p: Player):
            log(_p.get_rack_str())
            log(_p.get_temp_str())

        self.foreach_player(log_racks)

        self.game_state = GameState.BUY
        self.foreach_player(lambda _p: _p.set_state(PlayerState.PLAY),
                            lambda _p: _p.money >= p.rack.get_temp_value(),
                            lambda _p: _p.insufficient_balance())

        # if no players have the buying power, move to sell.
        if len(self.players_in_state(PlayerState.WAIT)) == len(self._players):
            self.game_state = GameState.SELL
            self.play_all()
            self.track(p, lambda gte: gte.update_msg(f"None of the players have buying power.",
                                                     NotificationType.WARN))

    def player_bought(self, p: Player, value=0):
        p.set_state(PlayerState.WAIT)
        in_play = self.players_in_state(PlayerState.PLAY)
        s_m = "You "
        o_m = f"{p.name} "
        if p.txn_status == Txn.BOUGHT:
            s_m += f"bought for ${value}"
            o_m += f"bought for ${value}"
        elif p.txn_status == Txn.BUY_CANCELLED:
            s_m += f"did not buy letters for ${value}"
            o_m += f"did not buy letters for ${value}"
        else:
            s_m += f"unexpected status {p.txn_status}"
            o_m += f"unexpected status {p.txn_status}"

        self.notify_all_players(p.number, s_m, o_m)
        self.track(p, lambda gte: gte.update_msg(o_m, value=value))

        if len(in_play) > 0:
            w_msg = 'Waiting for ' + ','.join(map(lambda tp: tp.name, in_play)) + ' to BUY'
            self.notify_waiting_players(w_msg)
            return

        self.game_state = GameState.SELL
        self.play_all()
        self.track(p, lambda gte: gte.update_msg("Buy complete.", NotificationType.ACT_2))

    def player_sold(self, p: Player, sold_word=[], value=0):
        p.set_state(PlayerState.WAIT)
        s_m = "You "
        o_m = f"{p.name} "

        word_str = ''.join(map(lambda t: t.letter, sold_word))

        if p.txn_status == Txn.SOLD:
            s_m += f"sold {word_str} for ${value}"
            o_m += f"sold {word_str} for ${value}"
        elif p.txn_status == Txn.SOLD_SELL_AGAIN:
            s_m += f"sold {word_str} for ${value}. \nmust sell {p.get_remaining_letters()} more letters"
            o_m += f"sold {word_str} for ${value}. \nmust sell {p.get_remaining_letters()} more letters"
        elif p.txn_status == Txn.SELL_CANCELLED_SELL_AGAIN:
            s_m += f"did not sell letters \nbut must sell {p.get_remaining_letters()} letters"
            o_m += f"did not sell letters \nbut must sell {p.get_remaining_letters()} letters."
            self.notify_all_players(p.number, s_m, o_m)
            self.track(p, lambda gte: gte.update_msg(s_m, value=value))
            return GameState.SELL
        elif p.txn_status == Txn.SELL_CANCELLED:
            s_m += f"did not sell letters."
            o_m += f"did not sell letters."
        else:
            s_m += f"unexpected status {p.txn_status}"
            o_m += f"unexpected status {p.txn_status}"

        self.notify_all_players(p.number, s_m, o_m)
        self.track(p, lambda gte: gte.update_msg(o_m, sold_word=word_str, value=value))

        in_play = self.players_in_state(PlayerState.PLAY)
        if len(in_play) > 0:
            w_msg = 'Waiting for ' + ','.join(map(lambda tp: tp.name, in_play)) + ' to SELL'
            self.notify_waiting_players(w_msg)
            return None

        m = f"Round {self.round} complete."
        self.foreach_player(lambda _p: _p.set_notify(NotificationType.ACT_2, m))
        self.set_roll()
        self.track(p, lambda gte: gte.update_msg(m, NotificationType.ACT_2))

    def player_left(self, p: Player):
        n_msg = f"{p.name} left"
        self.foreach_player(lambda _p: _p.set_inactive(),
                            lambda _p: _p.number == p.number,
                            lambda _p: _p.set_notify(NotificationType.WARN, n_msg))
        self.track(p, lambda gte: gte.update_msg(n_msg, NotificationType.ACT_2))

    def player_joined(self, p_num: int, team_id: int):
        pl = list(filter(lambda _p: _p.number == p_num and _p.team == team_id, self._players))
        if len(pl) != 1:
            raise RuntimeError(f"{p_num} player not found in {self}")
        player = pl[0]
        n_msg = f"{player.name} joined"
        self.foreach_player(lambda _p: _p.set_active(),
                            lambda _p: _p.number == player.number,
                            lambda _p: _p.set_notify(NotificationType.INFO, n_msg))
        self.track(player, lambda gte: gte.update_msg(n_msg, NotificationType.ACT_2))
        return player

    def play_all(self):
        self.foreach_player(lambda _o: _o.set_state(PlayerState.PLAY))

    def set_server_message(self, message):
        self.message = message

    def get_server_message(self):
        return self.message

    def get_game_bag(self):
        return self.bag

    """
    def notify_player_now_ready(self, player_joined):
        if len(self._players) != 2:
            return
        inactive_players = list(filter(lambda p: p is None or not p.active, self._players.values()))
        if len(inactive_players) == 0:
            self.ready = True
            log(f"game {self} is now ready")
            self.setServerMessage(f"{player_joined.name} joined")
        else:
            self.setServerMessage(f"Waiting for {' '.join(map(lambda _p: _p.name, inactive_players))}to join")

    def getCurrentPlayer(self):
        return self.currentPlayer

    def isReady(self):
        return self.ready

    def setClients(self, clients):
        self._players = clients

    def getPlayer(self, playerIndex):
        return self._players[playerIndex]

    def setPlayer(self, playerIndex):
        self.currentPlayer = playerIndex

    def checkReady(self):
        toCheck = self.getPlayers()
        notReady = []
        for player in toCheck:
            if player.played is True:
                continue
            else:
                notReady.append(player.get_name())
        return notReady

    def resetPlayed(self):
        for player in self._players.keys():
            self._players[player].played = False
        self.rolled = False

    def get_players_map(self) -> {int, Player}:
        return self._players

    def getPlayers(self):
        playersList = [self._players[_p] for _p in self._players.keys()]
        return playersList

    def setRacks(self, diceValue):
        for player in self.getPlayers():
            player.rack.add_to_rack(diceValue, self.bag)

    def setRolled(self):
        self.rolled = True

    def nextTurn(self):
        if self.currentPlayer == len(self._players) - 1:
            self.currentPlayer = self._players[0].number
        else:
            next_val = sorted(map(lambda p: p.number if p.number > self.currentPlayer else self.currentPlayer,
                                  self._players.values()))
            for i in next_val:
                if i == self.currentPlayer:
                    continue
                self.currentPlayer = i
                break
        log("nextTurn current player is now " + str(self.currentPlayer))
        # n = len(self._players)
        # if self.currentPlayer == n - 1:
        #     self.currentPlayer = 0
        # else:
        #     self.currentPlayer += 1
        self.turn += 1
        self.rolled = False
        self.resetPlayed()
    """

    def add_player(self, idx, player: Player):
        self._players.append(player)
        self.player_joined(player.number, player.team)
        # we need at least 2 players to start the game.
        if len(self._players) >= 2:
            self.set_roll()


class Rack:
    """
    Creates each player's 'dock', or 'hand'. Allows players to add, remove and replenish the number of tiles in their hand.
    """

    def __init__(self, nofw, bag):
        # Initializes the player's rack/hand. Takes the bag from which the racks tiles will come as an argument.
        self.rack = []
        self.temp = []
        # self.bag = bag
        # self.diceValue = diceValue
        self.add_wild_to_rack(nofw, bag)
        # self.initialize(diceValue)

        # self.get_temp_arr()
        # self.get_temp_value()

    # def setRack(self, bag, diceValue):
    #     self.bag = bag
    #     self.diceValue = diceValue

    def add_to_rack(self, diceValue, bag):
        # Takes a tile from the bag and adds it to the player's rack.
        for i in range(diceValue):
            self.temp.append(bag.take_from_bag())

    def rollback_rack(self, bag):
        value = self.get_temp_value()
        # for now stick to variation 1, whereby tiles are out of play
        # and doesn't returned to the bag
        self.get_temp_arr().clear()
        return value

    def add_wild_to_rack(self, nofw, bag):
        for i in range(nofw):
            self.rack.append(bag.take_wild_bag())

    def add_to_main(self):
        self.rack += self.temp
        self.temp = []

    # def initialize(self):
    #     # Adds the initial tiles to the player's hand.
    #     self.temp = []
    #     for i in range(self.diceValue):
    #         self.add_to_rack()

    def get_rack_str(self):
        # Displays the user's rack in string form.
        return ",".join(str(item.get_letter() if item is not None else "-") for item in self.rack)

    def get_rack_list(self):
        return [str(item.get_letter()) if item is not None else "" for item in self.rack]

    def get_rack_arr(self):
        # Returns the rack as an array of tile instances
        return self.rack

    def get_temp_str(self):
        # Displays the user's rack in string form.
        return ", ".join(str(item.get_letter()) for item in self.temp)

    def get_temp_arr(self):
        # Returns the rack as an array of tile instances
        return self.temp

    def remove_from_rack(self, tile):
        # Removes a tile from the rack (for example, when a tile is being played).
        self.rack.remove(tile)

    def clear_temp_rack(self):
        self.temp = []

    def get_temp_value(self):
        score = 0
        for tile in self.get_temp_arr():
            score += tile.score
        score = score * score
        # self.rackValue = score
        return score

    def get_rack_length(self):
        # Returns the number of tiles left in the rack.
        return len(self.get_rack_list())

    def replenish_rack(self):
        # Adds tiles to the rack after a turn such that the rack will have 7 tiles (assuming a proper number of tiles in the bag).
        while self.get_rack_length() < 7 and self.bag.get_remaining_tiles() > 0:
            self.add_to_rack()

    def updateGameBag(self, bag):
        self.bag = bag

    def num_non_wildcard_letters(self):
        return len(list(filter(lambda item: item is not None and item.letter != WILD_CARD, self.rack)))


class Tile:
    """
    Class that allows for the creation of a tile.
    Initializes using an uppercase string of one letter,
    and an integer representing that letter's score.
    """

    def __init__(self, tile_id, letter, game_tiles):
        # Initializes the tile class. Takes the letter as a string,
        # and the dictionary of letter values as arguments.
        self.t_id = tile_id
        self.letter = letter.upper()
        self.game_tiles = game_tiles
        if self.letter in game_tiles.loc[:, "VALUE"]:
            self.score = game_tiles.loc[self.letter, 'VALUE']
        else:
            self.score = 0

    def __repr__(self):
        return f"{self.t_id}-{self.letter}"

    def __copy__(self):
        return Tile(-1, self.letter, self.game_tiles)

    def set_tile_id(self, _id: int):
        self.t_id = _id

    def get_tile_id(self):
        return self.t_id

    def get_letter(self):
        # Returns the tile's letter (string).
        return self.letter

    def get_score(self):
        # Returns the tile's score value.
        return self.score


class Bag:
    """
    Creates the bag of all tiles that will be available during the game.
    Contains 108 letters and nine wild tiles.
    Takes no arguments to initialize.
    """

    def __init__(self, game_tiles):
        # Creates the bag full of game tiles,
        # and calls the initialize_bag() method,
        # which adds the default 100 tiles to the bag.
        # Takes no arguments.
        self.bag = []
        self.wildcard_bag = []
        self.tile_id = 0
        self.initialize_bag(game_tiles)

    def add_to_bag(self, tile: Tile, quantity):
        # Adds a certain quantity of a certain tile to the bag.
        # Takes a tile and an integer quantity as arguments.
        for i in range(quantity):
            copy_t = tile.__copy__()
            self.tile_id += 1
            copy_t.set_tile_id(self.tile_id)
            if copy_t.letter == WILD_CARD:
                self.wildcard_bag.append(copy_t)
            else:
                self.bag.append(copy_t)

    def initialize_bag(self, game_tiles):
        # Adds the intiial 108 tiles to the bag.
        for index, row in game_tiles.iterrows():
            # print(index, row['NO'], row['VALUE'])
            self.tile_id += 1
            self.add_to_bag(Tile(self.tile_id, index, game_tiles), row['NO'])

        shuffle(self.bag)

    def take_from_bag(self):
        # Removes a tile from the bag and returns it to the user.
        # This is used for replenishing the rack.
        return self.bag.pop()

    def return_to_bag(self, tile):
        if tile.letter == WILD_CARD:
            self.wildcard_bag.append(tile)
        else:
            self.bag.append(tile)

    def get_remaining_tiles(self):
        # Returns the number of tiles left in the bag.
        return len(self.bag)

    def take_wild_bag(self):
        return self.wildcard_bag.pop()


# function to simulate rolling dice
def dice_roll():
    choice = random.choice(dice)
    print("rolling dice...", choice)
    # print(choice)
    if choice == 'Your Choice':
        while choice not in [2, 3, 4, 5]:
            choice = int(input("Enter a number from 2-5:  "))
            if choice not in [2, 3, 4, 5]:
                print("invalid input. Please enter number from 2-5")
        # print(choice)
    print("")
    return choice
