# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 13:40:58 2021

@author: Boss
"""
import datetime
import signal
import socket
import os
# import thread module
import threading
import time
from _thread import *
from collections import deque
from threading import Event

import pandas as pd

# Creating a TCP socket
# AF_INET means IPV4
# SOCK_STREAM means TCP
import yaml

from common.game import *
from common.gameconstants import *
from common.logger import log
from datetime import datetime

from common.player import Player
from common.utils import serialize, receive_message, ObjectType, write_file
from server.server_utils import SignalHandler
from server.socket import ClientSocket

script_path = os.path.dirname(os.path.abspath(__file__))


class Server:
    def __init__(self):
        self.GAMETILES = pd.read_csv(os.path.join(script_path, "tiles.csv"), index_col="LETTER")
        # self.WordDict = pd.read_json(os.path.join(script_path, 'words_dictionary.json'), typ='series').index
        self.word_dict_csv = pd.read_csv(os.path.join(script_path, 'words_dictionary-2.csv'))  # , index_col='words')

        # self.IP = "localhost"
        self.IP = "0.0.0.0"
        self.PORT = 1234
        self.gameId = 0
        self.socket_timeout = 0
        write_file(SERVER_SETTINGS_FILE, lambda _f: yaml.safe_dump(SERVER_SETTINGS_TEMPLATE, _f))
        log(f"about to read {SERVER_SETTINGS_FILE}")
        with open(SERVER_SETTINGS_FILE) as fp:
            self.server_settings = yaml.safe_load(fp)
            self.server_defaults = self.server_settings['server_defaults']
            self.game_settings = self.server_settings['game_settings']
            self.IP = self.server_defaults['bind_ip']
            self.PORT = int(self.server_defaults['bind_port'])
            self.socket_timeout = int(self.server_defaults['socket_timeout'])
            self.gameId = int(self.game_settings['last_gen_id'])
            log(f"read SERVER SETTINGS {self.server_settings}")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEADDR  is being set to 1(true), if program is restarted TCP socket we created can be used again
        # without waiting for a for the socket to be fully closed.
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # binding socket and listening for connections
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen(4)
        if self.socket_timeout > 0:
            self.server_socket.settimeout(self.socket_timeout)
        self.pid = os.getpid()
        log(f"server started with pid={self.pid}")
        self.is_server_active = True
        self.nofw = 4
        self.client_sockets_list: [ClientSocket] = []
        self.threads_list: [threading.Thread] = []
        self.clients = {}
        self.number_of_usr = 0
        self.waitingForGameToStart = True
        self.games: [Game] = []
        self.number_of_usr = 0
        self.cleanup_interval = Event()
        self.handshake_lock = RLock()

    def signal_handler(self, sig, frame):
        if sig == signal.SIGINT or \
                sig == signal.SIGTERM:
            log(f"shutting down server pid={self.pid} with {sig}")
            self.is_server_active = False
            self.game_settings['last_gen_id'] = self.gameId
            with open(SERVER_SETTINGS_FILE) as fp:
                _p_settings = yaml.safe_load(fp)
                _p_settings['game_settings']['last_gen_id'] = self.game_settings['last_gen_id']

                def write_back(_fp):
                    log(f"with {_p_settings}")
                    yaml.safe_dump(_p_settings, _fp)

                write_file(SERVER_SETTINGS_FILE,write_back, overwrite=True)
            self.server_socket.close()  # will generate Bad file descriptor in socket.accept()
        elif sig == signal.SIGKILL:
            self.is_server_active = False
            self.server_socket.close()

    def main(self):
        # Waiting for players to join lobby and to start game
        try:
            # start_new_thread(self.cleanup_thread, ())
            ct = threading.Thread(target=self.cleanup_thread,
                                  name="cleanup-thread",
                                  daemon=True)
            ct.start()
            self.threads_list.append(ct)

            while self.is_server_active:
                log(f"server is listening on {self.IP}:{self.PORT}.....")
                client_socket, client_address = self.server_socket.accept()
                with self.handshake_lock:
                    client_socket.setblocking(True)
                    # adding client socket to list of users
                    log(f"[CONNECTION] {client_address} connected!")
                    cs = ClientSocket(client_socket, client_address)
                    g, player = self.handshake(cs)
                    if g is None:
                        cs.close(self.threads_list)
                        continue
                    cs.post_handshake(g.game_id, player)
                    self.client_sockets_list.append(cs)
                    # always send the game object as response and then may be other responses.
                    cs.socket.sendall(serialize(ObjectType.OBJECT, g))
                    log(f"game sent to client with session id {[player.session_id]}")
                    cs.socket.sendall(serialize(ObjectType.MESSAGE, player.session_id))
                    # cs.socket.sendall(create_pickle(g))
                    log("handshake complete")
                    # sending game to player
                    # start_new_thread(self.threaded, (cs, self.gameId))
                    ct = threading.Thread(target=self.threaded, args=(cs, g),
                                          name=cs.thread_name,
                                          daemon=False)
                    ct.start()
                    self.threads_list.append(ct)
                    self.number_of_usr += 1
        except OSError as ose:
            if ose.errno != 9:  # 9 = Bad file descriptor (generated due to socket.close())
                log("socket.error Terminating the server.", ose)
                raise
        except Exception as e:
            log("Unexpected exception. Terminating the server.", e)
            raise
        finally:
            self.cleanup_interval.set()
            for _cs in self.client_sockets_list:
                _cs.mark_inactive()

            for _ct in self.threads_list:
                _ct.join()

            self.server_socket.close()

    def threaded(self, _cs: ClientSocket, game: Game):
        assert _cs.player.game.game_id == game.game_id
        # c is socket
        stringp = str(_cs.player.number)
        log(f"ready to process messages")
        p = serialize(ObjectType.MESSAGE, stringp)
        decodedP = int(p.decode('utf-8')[-1])
        # _cs.socket.send(p)
        continuous_retries = MAX_RETRY
        while _cs.is_active:
            try:
                # data received from client
                payload: str = receive_message(_cs.socket)
                if payload is None or (isinstance(payload, bool) and not bool(payload)):
                    # slow down the next STREAM SOCKET read
                    time.sleep(1)
                    continuous_retries -= 1
                    if continuous_retries <= 0:
                        log(f"max_retry={MAX_RETRY} reached, closing unreachable socket {_cs}")
                        _cs.mark_inactive()
                    continue
                if VERBOSE:
                    log(f"received message payload [{payload}]")
                continuous_retries = MAX_RETRY
                with game.game_mutex:
                    self.handle_client_msg(_cs, decodedP, game, payload)
                    game.set_server_message(" ")
            except Exception as e:
                log("unknown error in client handling thread", e)
                # %%
                break
        _cs.player.game.player_left(_cs.player)
        # current_game: Game = self.games[_game_id]
        # players_map = dict(current_game.get_players_map())
        # removed_player: Player = players_map.pop(decodedP)
        # if removed_player:
        #     log(f"Removed {decodedP} from game's player_map")
        #
        # if decodedP == current_game.currentPlayer:
        #     log(f"closing current player {stringp} connection.")
        #     if len(players_map) > 0:
        #         _p: Player = random.choice(current_game.getPlayers())
        #         current_game.setPlayer(_p.number)
        #         current_game.setReady(_p.number)
        #         self.games[_game_id] = current_game
        # else:
        #     log(f"closing client {stringp} connection.")

        log(f"closing client {stringp} connection.")
        self.number_of_usr -= 1
        # connection closed
        _cs.close(self.threads_list)

    def cleanup_thread(self):
        while not self.cleanup_interval.is_set():
            curr_ts = datetime.now()

            # handle stale client socket
            i = len(self.client_sockets_list) - 1
            while i >= 0:
                log(f"i = {i} and cslist = {len(self.client_sockets_list)}") if VERBOSE else None
                _cs = self.client_sockets_list[i]
                # if we miss 5 heartbeats in a row, time to close that socket
                x = (curr_ts - _cs.last_hb_received).total_seconds()
                y = (HEARTBEAT_INTERVAL_SECS * 5.0)
                if x > y:
                    log(f"Cleaning up player {_cs} socket, last hb received @{_cs.last_hb_received}")
                    stale = self.client_sockets_list.pop(i)
                    stale.mark_inactive()
                i -= 1

            # handle stale game objects
            with self.handshake_lock:
                i = len(self.games) - 1
                while i >= 0:
                    _g: Game = self.games[i]
                    # if the game is paused for too long (15 mins default)
                    x = (curr_ts - _g.last_activity_time).total_seconds()
                    if _g.game_status == GameStatus.PAUSED and x > _g.max_idle_secs:
                        # timedelta(0,_g.max_idle_secs).__str__()
                        log(f"Cleaning up game {_g} after {_g.max_idle_secs/60:.02f} min(s),"
                            f"last_activity @{_g.last_activity_time}")
                        stale = self.games.pop(i)
                        with stale.game_mutex:
                            stale.abandon_game()
                    elif _g.game_status == GameStatus.COMPLETED:
                        complete = self.games.pop(i)
                        with complete.game_mutex:
                            complete.close()

                    i -= 1

            self.cleanup_interval.wait(HEARTBEAT_INTERVAL_SECS)

    def handle_client_msg(self, _cs: ClientSocket, decoded_p: int,
                          game: Game,
                          payload: str):
        # if _game_id in games:
        # current_game = game
        # if bool(payload) is not False:
        import re
        m = re.match('^(.*?):(.*?)$', payload, re.M)
        if m is None:
            (msg_enum, data) = payload.split(':')
        else:
            (msg_enum, data) = (m.group(1), m.group(2))

        log(f"client request: {msg_enum} - {data}") if msg_enum not in ClientMsgReq.HeartBeat.msg else None
        client_req: ClientMsgReq = ClientMsgReq.parse_msg_string(msg_enum + ':')
        game.set_last_activity_ts()

        try:
            if ClientMsgReq.HeartBeat == client_req:
                log("sending heartbeat response") if VERBOSE else None
                _cs.socket.sendall(serialize(ObjectType.MESSAGE, ClientMsgReq.HeartBeat.msg))
                _cs.set_last_active_ts()
                return

            elif ClientMsgReq.Dice == client_req:
                diceValue = int(data)
                log(f"diceValue is {diceValue}")
                if game.is_invalid_op(_cs.player, "cannot roll"):
                    game.set_server_message(ClientResp.Cannot_Roll.msg)
                    return
                game.player_rolled(_cs.player, diceValue)
                game.set_server_message(ClientResp.Racks_Ready.msg)

            elif ClientMsgReq.Get == client_req:
                msgs_notified_upto = int(str(data).lstrip("notifications_received="))
                _q: deque = _cs.player.notify_msg
                while _q.__len__() > 0:
                    n = _q.__iter__().__next__()
                    if n.n_id <= msgs_notified_upto:
                        _popped_m = _cs.player.notify_msg.popleft()
                        if VERBOSE:
                            log(f"discarding notify msg {_popped_m}")
                    else:
                        break
                game.set_server_message(f"{_cs.player}")

            elif ClientMsgReq.Buy == client_req:
                if game.is_invalid_op(_cs.player, "cannot buy"):
                    game.set_server_message(ClientResp.Cannot_Buy.msg)
                    return

                try:
                    _cs.player.buy_word()
                    game.set_server_message(f"{ClientResp.Bought.msg} Player {decoded_p}")
                except Exception as e:
                    log(f"{game} {_cs.player} buy failed", e)

            elif ClientMsgReq.Skip_Buy == client_req:
                try:
                    _cs.player.skip_buy(game.bag)
                    game.set_server_message(f"{ClientResp.Buy_Skipped.msg} Player {decoded_p}")
                except Exception as e:
                    log(f"{game} {_cs.player} buy cancellation failed", e)

            elif ClientMsgReq.Sell == client_req:
                try:
                    word = data
                    _cs.player.sell(word, self.word_dict_csv)
                    if _cs.player.txn_status == Txn.MUST_SELL:
                        game.set_server_message(f"{ClientResp.Must_Sell.msg} word={word}")
                    elif _cs.player.txn_status == Txn.SOLD:
                        game.set_server_message(f"{ClientResp.Sold.msg} word={word}")
                    elif _cs.player.txn_status == Txn.SELL_FAILED:
                        game.set_server_message(f"{ClientResp.Sell_Failed.msg} word={word}")
                except Exception as e:
                    log(f"{game} {_cs.player} sell failed", e)

            elif ClientMsgReq.Discard_Sell == client_req:
                word = data
                _cs.player.discard_sell(word)
                if _cs.player.txn_status == Txn.SELL_DISCARDED:
                    game.set_server_message(f"{ClientResp.Sell_Discarded.msg} Player {decoded_p}")

            elif ClientMsgReq.EndTurn == client_req:
                _cs.player.end_turn()
                if _cs.player.txn_status == Txn.MUST_SELL:
                    game.set_server_message(f"{ClientResp.Must_Sell.msg} Player {decoded_p}")
                elif _cs.player.txn_status == Txn.TURN_COMPLETE:
                    game.set_server_message(f"{ClientResp.Turn_Ended.msg} Player {decoded_p}")

            elif ClientMsgReq.PostGameSurvey == client_req:
                msg = data
                _cs.player.player_post_game_survey(msg)
                game.set_server_message(f"{ClientResp.PostGameSurveyDone.msg} Player {decoded_p}")

        finally:
            # self.games[_game_id] = current_game
            serverMessage = game.get_server_message()
            if len(serverMessage.strip()) > 0:
                log(f"serverMessage: {serverMessage} ")
            _cs.socket.sendall(serialize(ObjectType.OBJECT, game))
            _cs.set_last_active_ts()
            # game.set_server_message(" ")

    def handshake(self, cs: ClientSocket):
        retries = MAX_RETRY
        while self.is_server_active:
            payload = receive_message(cs.socket, True)
            if not bool(payload):
                if retries > 0:
                    retries -= 1
                    continue
                else:
                    return None, None
            retries = MAX_RETRY
            log(f"handshake: received msg: {payload}")
            (msg_enum, data) = payload.split(':')
            client_req: ClientMsgReq = ClientMsgReq.parse_msg_string(msg_enum + ':')
            assert ClientMsgReq.SessionID == client_req

            import re
            parts = re.findall("\\[([^[\\]]*)\\]", str(data))

            def split_get(idx):
                return parts[idx].split('=')[1]

            # if only player name is received.
            if len(parts) == 1:
                game_id = -1
                begin_time = ""
                team_id = 0
                player_id = -1
                player_name = parts[0]
            else:
                game_id = int(split_get(0))
                team_id = int(split_get(1))
                player_id = int(split_get(2))
                player_name = parts[3]
                begin_time = parts[4]

            g = None
            for _g in self.games:
                if _g.game_status.value < GameStatus.ABANDONED.value and \
                        _g.game_id == game_id:  # and _g.begin_time == begin_time:
                    g = _g
                    break

            def get_latest_unpaired_game():
                if len(self.games) == 0:
                    return None

                open_games = list(filter(lambda _g: _g.game_status.value < GameStatus.ABANDONED.value
                                         and len(_g.players()) == 1
                                         and _g.players()[0].name != player_name,
                                         self.games))
                if len(open_games) > 0:
                    latest_g = open_games[0]
                    return latest_g

                return None

            player = None
            # if requested game of the player don't exists anymore.
            if g is None:
                unpaired_game = get_latest_unpaired_game()
                if unpaired_game is not None:
                    typed_g: Game = unpaired_game
                    player_id = 1
                    player = Player(typed_g, int(nofw), player_id, player_name, team_id,
                                    unpaired_game.get_game_bag())
                    typed_g.add_player(player_id, player)
                    log(f"attaching new player {player} to an existing game {unpaired_game}")
                    g = typed_g
                    game_id = typed_g.game_id
                    begin_time = typed_g.begin_time
                else:
                    self.gameId = self.gameId + 1
                    g = Game(self.gameId, self.game_settings, self.GAMETILES)
                    game_id = g.game_id
                    begin_time = g.begin_time
                    log(f"created a new game.... {g}")
                    self.games.append(g)
                    player_id = 0
                    # Giving player their own socket in dictionary
                    player = Player(g, int(nofw), player_id, player_name, team_id,
                                    g.get_game_bag())
                    # putting player in game
                    g.add_player(player_id, player)
                    player.set_notify(NotificationType.INFO, "Waiting for another player to join")
                    log(f"created first player {player} {g}")
            else:
                assert isinstance(g, Game)
                player = g.player_joined(player_id, team_id)
                assert player.session_id == str(data)
                log(f"resuming for player {player} in an existing game {g}")

            def create_session_id():
                return str(f"[g={game_id}]-[t={team_id}]-[p={player_id}]-"
                           f"[{player_name}]-[{begin_time}]")

            player.client_ip_address = cs.c_addr[0]
            g.set_server_message(f"{player.name} handshake complete")
            player.session_id = create_session_id()
            return g, player




if __name__ == '__main__':
    s = Server()
    with SignalHandler(s.signal_handler):
        s.main()
