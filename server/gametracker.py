import csv
import os
from datetime import datetime
from enum import Enum, auto

from common.logger import log
from common.player import Player
from common.gameconstants import GameStage, PlayerState, Txn, NotificationType, GameStatus
from common.utils import calling_func_name, write_file


class GameTracker:
    def __init__(self, game_settings, g_id):
        log(f"creating game with settings {game_settings}")
        self.tracker_filename = os.path.join(game_settings['store_path'], f"{g_id:04d}-{os.getpid()}.csv")
        log(f"tracking game into {self.tracker_filename}")
        # self.track_file = open(self.tracker_filename, 'a', True)
        write_file(self.tracker_filename, GameTrackerEntry.write_to_csv)
        self.tracker_file = open(self.tracker_filename, 'a', True)
        self.gte = GameTrackerEntry()

    def track(self, g, p: Player, cb):
        if self.tracker_file is None:
            return
        from common.game import Game
        assert isinstance(g, Game)
        self.gte.update_game(g)
        self.gte.update_player(p)
        if cb is not None:
            cb(self.gte)
        self.gte = self.gte.commit(self.tracker_file, g)

    def close(self):
        self.tracker_file.close()
        self.tracker_file = None


class GameTrackerEntry:
    def __init__(self):
        self.game_id = ""
        self.round = -1
        self.game_stage = GameStage.INIT
        self.game_status = GameStatus.START
        self.game_last_activity_time = ""
        self.timestamp = ""
        self.session_id = ""
        self.player_name = ""
        self.player_ip_address = ""
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

    def get_column_names(self):
        return self.__dict__.keys()

    def __repr__(self):
        return ','.join(self.__dict__.values())

    def _internal_dup_entry(self, g):
        entry = self.__new__(GameTrackerEntry)
        entry.update_game(g)
        # entry.game_id = self.game_id
        # entry.game_state = self.game_state
        return entry

    def update_game(self, g):
        from common.game import Game
        assert isinstance(g, Game)
        self.game_id = g.game_id
        self.round = g.round
        self.game_stage = g.game_stage
        self.game_status = g.game_status
        self.game_last_activity_time = g.last_activity_time.strftime("%m/%d %H:%M:%S")

    def update_player(self, p: Player, value: int = 0):
        self.session_id = p.session_id
        self.player_name = p.name
        self.player_ip_address = str(p.client_ip_address)
        self.player_state = p.player_state
        self.txn_status = p.txn_status
        self.action = calling_func_name(3)
        self.player_money = p.money
        self.buy_rack = p.rack.get_temp_str()
        self.current_rack = p.rack.get_rack_str()
        if value > 0:
            self.letters_value = value

    def update_msg(self, msg: str, msg_type: NotificationType = NotificationType.INFO,
                   dice_rolled: int = 0, sold_word: str = "", value: int = 0, buy_rack=[]):
        self.message_type = msg_type
        self.message = msg
        if dice_rolled > 0:
            self.dice_rolled = dice_rolled
        if len(sold_word) > 0:
            self.sold_word = sold_word
        if value > 0:
            self.letters_value = value
        if len(buy_rack) > 0:
            self.buy_rack = buy_rack
        from common.game import get_current_timestamp
        self.timestamp = get_current_timestamp()

    @classmethod
    def write_to_csv(cls, fp):
        csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC).writerow(
            GameTrackerEntry().get_column_names()
        )

    def commit(self, file, g):
        from common.game import Game
        assert isinstance(g, Game)
        csv.writer(file, quoting=csv.QUOTE_NONNUMERIC).writerow(
            self.__dict__.values()
        )
        file.flush()
        return self._internal_dup_entry(g)

