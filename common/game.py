# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 11:44:56 2021

@author: Boss
"""
import os.path
import random
from datetime import datetime
from threading import RLock

from common.bag import Bag
from common.gameconstants import WILD_CARD, NL_DELIM, NotificationType, Txn, \
    PlayerState, GameStage, GameStatus, ConnectionStatus
from common.logger import log
from common.player import Player
from server.gametracker import GameTrackerEntry, GameTracker

nofw = 4
# import player as pl
# defining game dice
dice = ['2', '3', '4', '5', 'Your Choice', 'Your Choice']
# will store values of user
myTiles = []


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


def get_current_timestamp():
    return datetime.now().strftime("%m/%d %H.%M.%S")


class Game:
    def __init__(self, g_id, game_settings, game_tiles):
        self.game_id = g_id
        self.game_settings = game_settings
        self._players: [Player] = []
        self.bag = Bag(game_tiles)
        self.turn = 0
        self.round = 0
        self.message = ""
        self.begin_time = get_current_timestamp()
        self.last_activity_time = datetime.now()
        self.game_stage = GameStage.INIT
        self.game_status = GameStatus.START
        self.game_tracker = GameTracker(game_settings, self.game_id)
        self.game_mutex = RLock()
        self.max_idle_secs = int(game_settings['cleanup_game_idle_secs'])

    def __repr__(self):
        return f"{self.game_id}-[{self.begin_time}]-{self.game_stage}"

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

    def notify_all_players(self, p_number, self_msg, other_msg,
                           self_notify_type=NotificationType.ACT_1,
                           others_notify_type=NotificationType.ACT_2):
        self.foreach_player(lambda _p: _p.set_notify(others_notify_type, other_msg),
                            lambda _p: _p.number != p_number,
                            lambda _p: _p.set_notify(self_notify_type, self_msg))

    def has_all_players(self, bool_condition):
        for _p in self._players:
            if not bool_condition(_p):
                return False
        return True

    def set_roll(self):
        self.game_stage = GameStage.ROLL
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
        o_msg = f"{p.name} needs to roll the dice, waiting."
        self.notify_all_players(p.number, s_msg, o_msg)
        self.track(p, lambda gte: gte.update_msg(o_msg))

    def track(self, p: Player, cb=None):
        self.game_tracker.track(self, p, cb)

    def players_in_state(self, s) -> list:
        return list(filter(lambda p: p.player_state == s, self._players))

    def player_rolled(self, plyr: Player, dice_value: int):
        n = len(self.players())
        if self.bag.get_remaining_tiles() < (
                dice_value * n):
            err_msg = f"cannot draw {dice_value}*{n} out of {self.bag.get_remaining_tiles()} letters."
            log(f"insufficient {dice_value} letters for {n} players in bag."
                f"{NL_DELIM}remaining={self.bag.get_remaining_tiles()}")

            def set_player_endstate(_p: Player):
                _p.set_notify(NotificationType.ERR, err_msg)
                _p.set_state(PlayerState.PLAY)
                _p.txn_status = Txn.BAG_EMPTY

            self.foreach_player(set_player_endstate)
            self.game_stage = GameStage.END_SELL_ONLY
            self.track(plyr, lambda gte: gte.update_msg(err_msg, NotificationType.ERR))
            return self.game_stage

        # %% we have enough, are racks initialized?
        # giving racks their bag and dice values
        try:
            self.foreach_player(lambda _p: _p.rack.clear_temp_rack())
        except Exception as e:
            log(f"{self} clear rack failed: ", e)

        self.foreach_player(lambda _p: _p.rack.add_to_rack(dice_value, self.bag))

        log(f"{self} handed racks to all")

        def set_dice_rolled(_p: Player):
            _p.txn_status = Txn.ROLLED
            log(_p.get_rack_str())
            log(_p.get_temp_str())

        self.foreach_player(set_dice_rolled)

        self.game_stage = GameStage.BUY
        self.foreach_player(lambda _p: _p.set_state(PlayerState.PLAY),
                            lambda _p: _p.money >= _p.rack.get_temp_value(),
                            lambda _p: _p.insufficient_balance())

        self.track(plyr, lambda gte: gte.update_msg(f"{plyr.name} rolled dice to {dice_value}",
                                                    dice_rolled=dice_value))

        # if no players have the buying power, move to sell.
        if len(self.players_in_state(PlayerState.WAIT)) == len(self._players):
            self.game_stage = GameStage.SELL
            self.play_all()
            self.track(plyr, lambda gte: gte.update_msg(f"None of the players have buying power.",
                                                        NotificationType.WARN))

    def player_buying(self, p: Player, value=0, buy_rack=[]):
        p.set_state(PlayerState.WAIT)
        s_m = "You "
        o_m = f"{p.name} "
        if p.txn_status == Txn.BOUGHT:
            s_m += f"bought for ${value}"
            o_m += f"bought for ${value}"
        elif p.txn_status == Txn.BUY_SKIPPED:
            s_m += f"did not buy letters for ${value}"
            o_m += f"did not buy letters for ${value}"
        else:
            s_m += f"buying unexpected status {p.txn_status}"
            o_m += f"{p.name} buying unexpected status {p.txn_status}"

        self.notify_all_players(p.number, s_m, o_m)
        self.track(p, lambda gte: gte.update_msg(o_m, value=value, buy_rack=buy_rack))

        in_play = self.players_in_state(PlayerState.PLAY)
        if len(in_play) > 0:
            w_msg = 'Waiting for ' + ','.join(map(lambda tp: tp.name, in_play)) + ' to BUY'
            self.notify_waiting_players(w_msg)
            return

        self.game_stage = GameStage.SELL
        self.play_all()
        # self.track(p, lambda gte: gte.update_msg("Buy complete.", NotificationType.ACT_2))

    def player_selling(self, p: Player, word_str="", word_regex="", value=0):
        s_notify_t = NotificationType.ACT_1
        if p.txn_status == Txn.SOLD:
            s_m = f"you sold {word_str} for ${value}"
            o_m = f"{p.name} sold {word_str} for ${value}"
            # p.set_state(PlayerState.WAIT)
        # elif p.txn_status == Txn.SELL_AGAIN:
        #     s_m = f"you sold {word_str} for ${value}." \
        #           f"{NL_DELIM}must sell {p.get_remaining_letters()} more letters"
        #     o_m = f"{p.name} sold {word_str} for ${value}." \
        #           f"{NL_DELIM}must sell {p.get_remaining_letters()} more letters"
        #     p.set_state(PlayerState.PLAY)
        #     s_notify_t = NotificationType.ERR
        # elif p.txn_status == Txn.SELL_CANCELLED_SELL_AGAIN:
        #     s_m = f"you did not sell any letters" \
        #           f"{NL_DELIM}but must sell {p.get_remaining_letters()} more letters"
        #     o_m = f"{p.name} did not sell any letters" \
        #           f"{NL_DELIM}but must sell {p.get_remaining_letters()} more letters."
        #     s_notify_t = NotificationType.ERR
        #     p.set_state(PlayerState.PLAY)
        elif p.txn_status == Txn.SELL_DISCARDED:
            s_m = f"you discarded {word_str} to sell."
            o_m = f"{p.name} discarded {word_str} to sell."
            # p.set_state(PlayerState.WAIT)
        elif p.txn_status == Txn.NO_SELL:
            num_wild_cards = len(word_str.split(WILD_CARD))
            if num_wild_cards > 2:
                s_m = f"You cannot have {num_wild_cards-1} wild cards" \
                      f"{NL_DELIM}in a word, only 1 allowed."
                o_m = f"{p.name} cannot have {num_wild_cards-1} wild cards" \
                      f"{NL_DELIM}in a word, only 1 allowed."
            else:
                s_m = f"your word {word_str}{NL_DELIM}doesn't exists"
                o_m = f"{p.name}'s word {word_str}{NL_DELIM}doesn't exists"
            s_notify_t = NotificationType.ERR
            # p.set_state(PlayerState.WAIT)
        else:
            s_m = f"selling unexpected status {p.txn_status}"
            o_m = f"{p.name} selling unexpected status {p.txn_status}"
            s_notify_t = NotificationType.ERR

        p.set_state(PlayerState.PLAY)
        self.notify_all_players(p.number, s_m, o_m, self_notify_type=s_notify_t)
        self.track(p, lambda gte: gte.update_msg(o_m, sold_word=word_str, value=value))

        # in_play = self.players_in_state(PlayerState.PLAY)
        # if len(in_play) > 0:
        #     w_msg = 'Waiting for ' + ','.join(map(lambda tp: tp.name, in_play)) + ' to SELL'
        #     self.notify_waiting_players(w_msg)
        #     return None
        #
        # if p.txn_status == Txn.SELL_AGAIN \
        #         or p.txn_status == Txn.SELL_CANCELLED_SELL_AGAIN \
        #         or p.txn_status == Txn.NO_SELL:
        #     return

    def player_try_turn_complete(self, p: Player):
        s_notify_t = NotificationType.ACT_1
        if p.txn_status == Txn.MUST_SELL:
            s_m = f"Cannot End Turn." \
                  f"{NL_DELIM}You must sell {p.get_remaining_letters()} more letters"
            o_m = f"Cannot Finish Round." \
                  f"{NL_DELIM}{p.name} must sell {p.get_remaining_letters()} more letters"
            p.set_state(PlayerState.PLAY)
            s_notify_t = NotificationType.ERR
            self.notify_all_players(p.number,
                                    s_m, o_m, self_notify_type=s_notify_t)
            self.track(p, lambda gte: gte.update_msg(s_m))
            return

        p.set_state(PlayerState.WAIT)
        in_play = self.players_in_state(PlayerState.PLAY)
        if len(in_play) > 0:
            w_msg = 'Waiting for ' + ','.join(map(lambda tp: tp.name, in_play)) + ' to finish turn'
            self.notify_waiting_players(w_msg)
            return None

        if self.game_stage == GameStage.END_SELL_ONLY:
            self.game_stage = GameStage.TERMINATE
            self.game_status = GameStatus.COMPLETED
            get_winner = self._players.copy()
            get_winner.sort(key=lambda _p: _p.money, reverse=True)
            m = f"{get_winner[0].name} is the winner!."
            self.foreach_player(lambda _p: _p.set_notify(NotificationType.FLASH, m))
            self.track(p, lambda gte: gte.update_msg(m, NotificationType.FLASH))
            return

        m = f"Round {self.round} complete."
        self.game_stage = GameStage.ROUND_COMPLETE
        self.foreach_player(lambda _p: _p.set_notify(NotificationType.ACT_2, m))
        self.track(p, lambda gte: gte.update_msg(m, NotificationType.ACT_2))
        self.set_roll()

    def player_left(self, p: Player):
        n_msg = f"{p.name} left"
        self.foreach_player(lambda _p: _p.set_inactive(),
                            lambda _p: _p.number == p.number,
                            lambda _p: _p.set_notify(NotificationType.ACT_2, n_msg))
        self.track(p, lambda gte: gte.update_msg(n_msg, NotificationType.ACT_2))
        if self.has_all_players(lambda _p: _p.p_conn_status == ConnectionStatus.LEFT):
            self.game_status = GameStatus.PAUSED
        self.last_activity_time = datetime.now()

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

        if self.has_all_players(lambda _p: _p.p_conn_status == ConnectionStatus.CONNECTED):
            self.game_status = GameStatus.RUNNING
        elif self.game_status == GameStatus.PAUSED:
            self.game_status = GameStatus.RESUMED
        self.last_activity_time = datetime.now()
        return player

    def play_all(self):
        self.foreach_player(lambda _o: _o.set_state(PlayerState.PLAY))

    def set_server_message(self, message):
        self.message = message

    def get_server_message(self):
        return self.message

    def get_game_bag(self):
        return self.bag

    def set_last_activity_ts(self):
        self.last_activity_time = datetime.now()

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

    def is_invalid_op(self, p: Player, err_msg: str):
        if self.game_stage == GameStage.END_SELL_ONLY and (
                p.txn_status != Txn.BUY_SKIPPED or
                p.txn_status != Txn.SELL_DISCARDED
        ):
            p.set_notify(NotificationType.ERR, "Game ending: " + err_msg)
            return True
        return False

    def abandon_game(self):
        self.game_status = GameStatus.ABANDONED
        self.foreach_player(lambda _p: self.track(_p))
        self.close()

    def close(self):
        self.game_tracker.close()


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
