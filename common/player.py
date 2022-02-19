from collections import deque

from common.rack import Rack
from common.gameconstants import *
from common.logger import log


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
        self.client_ip_address = ""
        self.name = name
        self.p_conn_status = ConnectionStatus.INIT
        self.rack = Rack(nofw, bag)
        self.money = int(self.game.game_settings['player_start_money'])
        self.team = team
        self.txn_status = Txn.INIT
        self.wordvalue = 0
        self.message = ""
        self.played = False
        self.start = False
        from common.game import Notification
        self.notify_msg: deque[Notification] = deque([], 20)
        self.player_state = PlayerState.WAIT
        self.notification_id = 0
        self.session_id = ""

    def __repr__(self):
        return f"gid={self.game.game_id} {self.game.game_stage} p={self.number} {self.player_state} " \
               f"{self.txn_status} {self.p_conn_status}"

    def set_name(self, name):
        # Sets the player's name.
        self.name = name

    def set_state(self, s):
        self.player_state = s

    def set_notify(self, n_type: NotificationType, msg: str):
        from common.game import Notification
        self.notify_msg.append(Notification(self.notification_id, n_type, msg))
        self.notification_id += 1

    def set_start(self):
        # Sets the player's name.
        self.start = True

    def get_name(self):
        # Gets the player's name.
        return self.name

    def set_active(self):
        self.p_conn_status = ConnectionStatus.CONNECTED

    def set_inactive(self):
        self.p_conn_status = ConnectionStatus.LEFT

    def insufficient_balance(self):
        msg = f"${self.money} not enough to buy" \
              f"{NL_DELIM}{self.rack.get_temp_str()} for ${self.rack.get_temp_value()}"
        self.set_notify(NotificationType.ERR,
                        msg)
        cleared_rack = self.rack.clear_temp_rack()
        self.player_state = PlayerState.WAIT
        self.txn_status = Txn.NO_BUY
        self.game.track(self, lambda gte: gte.update_msg(msg, NotificationType.ERR,
                                                         buy_rack=cleared_rack))

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
        buy_rack = self.rack.add_to_main()
        self.txn_status = Txn.BOUGHT
        self.game.player_buying(self, cost, buy_rack)
        return self

    def skip_buy(self, bag):
        value = self.rack.rollback_rack(bag)
        self.txn_status = Txn.BUY_SKIPPED
        self.game.player_buying(self, value)

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

    def _get_sellable_word(self, word, remove=True):
        word = word.upper()
        sell_word = []
        for w in word:
            if w in self.get_rack_list():
                for tile in self.get_rack_arr():
                    if w == tile.letter:
                        sell_word.append(tile)
                        if remove:
                            self.rack.remove_from_rack(tile)
                        break
            else:
                for tile in self.get_rack_arr():
                    if WILD_CARD == tile.letter:
                        sell_word.append(tile)
                        if remove:
                            self.rack.remove_from_rack(tile)
                        break
        return sell_word

    import pandas as pd

    def sell(self, word: str, word_dict: pd.DataFrame):
        from common.game import word_value
        # only 1 wild character is allowed in a single word.
        ret_val = None
        search_wrd = '^' + word.replace(WILD_CARD, ".", 1).lower() + '$'
        _found = word_dict[word_dict['words'].str.contains(search_wrd, regex=True).fillna(False)].count()
        if int(_found.values[0]) > 0:
            can_sell = self.word_check(word)
            if can_sell:
                sold_word = self._get_sellable_word(word)
                value = int(word_value(sold_word))
                self.money += value
                # if self.get_remaining_letters() > 0:
                #     self.txn_status = Txn.MUST_SELL
                # else:
                self.txn_status = Txn.SOLD
                ret_val = self.game.player_selling(self, ''.join(map(lambda t: t.letter, sold_word)),
                                                   word_regex=search_wrd,
                                                   value=value)
        else:
            num_wild_cards = len(word.split(WILD_CARD))
            if num_wild_cards > 2:
                msg = f"have {num_wild_cards-1} wild cards " \
                      f"in a word, only 1 allowed."
            else:
                msg = f"{word} (regex={search_wrd}) " \
                      f"doesn't exists."
            log(msg)
            self.txn_status = Txn.NO_SELL
            ret_val = self.game.player_selling(self, word, search_wrd)

        return ret_val

    def discard_sell(self, word: str):
        # if self.get_remaining_letters() > 0:
        #     self.txn_status = Txn.SELL_CANCELLED_SELL_AGAIN
        # else:
        self.txn_status = Txn.SELL_DISCARDED
        word_tile = self._get_sellable_word(word, False)

        from common.game import word_value
        self.game.player_selling(self, word, int(word_value(word_tile)))

    def get_remaining_letters(self):
        return self.rack.num_non_wildcard_letters() - MAX_LETTERS_ON_HOLD

    def end_turn(self):
        if self.get_remaining_letters() > 0:
            self.txn_status = Txn.MUST_SELL
        else:
            self.txn_status = Txn.TURN_COMPLETE

        self.game.player_try_turn_complete(self)