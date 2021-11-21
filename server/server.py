# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 13:40:58 2021

@author: Boss
"""
import datetime
import pickle
import random
import socket
import os
# import thread module
import threading
import time
from _thread import *
from threading import Event

import pandas as pd

# Creating a TCP socket
# AF_INET means IPV4
# SOCK_STREAM means TCP
from common.game import *
from common.gameconstants import *
from common.logger import log
from datetime import  datetime

from server.socket import ClientSocket

script_path = os.path.dirname(os.path.abspath(__file__))

def createMessage(message):
    message = f"{len(message):<{MSG_HEADER_LENGTH}}".encode(
        'utf-8') + message.encode('utf-8')
    return message


def createPickle(aPickle):
    aPickled = pickle.dumps(aPickle)
    aPickled = bytes(f"{len(aPickled):<{SERIALIZE_HEADER_LENGTH}}".encode(
        'utf-8') + aPickled)
    return aPickled


def receive_message(_cs) -> str:
    try:
        message_header = _cs.recv(MSG_HEADER_LENGTH)
        if not len(message_header):
            return None
        message = message_header.decode('utf-8').strip()
        return str(message)
    except Exception as e:
        log("receive message from client failed", e)
        return None


def receive_pickle(client_socket):
    try:
        message_header = client_socket.recv(SERIALIZE_HEADER_LENGTH)
        if not len(message_header):
            return False
        # print("first", message_header)
        message_length = int(message_header.decode('utf-8').strip())
        message = client_socket.recv(message_length)
        # print("message", message)
        unpickled = pickle.loads(message)
        # print("unpickled", unpickled)
        return unpickled
    except Exception as e:
        log("receive pickle from client failed", e)
        return False


class Server:
    def __init__(self):
        self.GAMETILES = pd.read_csv(os.path.join(script_path, "tiles.csv"), index_col="LETTER")
        # bag = GAMETILES
        # self.WordDict = pd.read_json(os.path.join(script_path, 'words_dictionary.json'), typ='series').index
        self.word_dict_csv = pd.read_csv(os.path.join(script_path, 'words_dictionary-2.csv'))  # , index_col='words')

        HEADER_LENGTH = 2048
        self.IP = "localhost"
        self.PORT = 1234
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEADDR  is being set to 1(true), if program is restarted TCP socket we created can be used again
        # without waiting for a for the socket to be fully closed.
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # binding socket and listening for connections
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen(4)
        log("server started.....")
        self.nofw = 4
        self.client_sockets_list: [ClientSocket] = []
        self.threads_list: [threading.Thread] = []
        self.clients = {}
        self.number_of_usr = 0
        self.waitingForGameToStart = True
        self.games: [int, Game] = {}
        self.gameId = 0
        self.number_of_usr = 0
        self.cleanup_interval = Event()

    def main(self):
        # Waiting for players to join lobby and to start game
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                client_socket.setblocking(True)
                # adding client socket to list of users
                log(f"[CONNECTION] {client_address} connected!")
                cs = ClientSocket(client_socket, len(self.client_sockets_list))
                self.client_sockets_list.append(cs)
                if self.number_of_usr == 0:
                    log("Creating a new game....")
                    self.games[self.gameId] = Game(self.gameId, self.GAMETILES)
                    # start_new_thread(self.cleanup_thread, ())
                    ct = threading.Thread(target=self.cleanup_thread,
                                          name="cleanup-thread",
                                          daemon=True)
                    ct.start()
                    self.threads_list.append(ct)

                log("creating player object...")
                # Giving player their own socket in dictionary
                self.clients[self.number_of_usr] = Player(int(nofw), int(self.number_of_usr),
                                                          self.games[self.gameId].getGameBag())
                # putting player in game
                log("player created")
                self.games[self.gameId].setClients(self.clients)
                log("setting clients to game \n sending game to client")
                # sending game to player
                # start_new_thread(self.threaded, (cs, self.gameId))
                ct = threading.Thread(target=self.threaded, args=(cs, self.gameId),
                                      name="client-" + str(self.number_of_usr),
                                      daemon=False)
                ct.start()
                self.threads_list.append(ct)
                log("game sent to client ")
                self.number_of_usr += 1
        finally:
            self.cleanup_interval.set()
            for _cs in self.client_sockets_list:
                _cs.mark_inactive()

            for _ct in self.threads_list:
                _ct.join()

            self.server_socket.close()

    def threaded(self, _cs: ClientSocket, _game_id):
        # c is socket
        stringp = str(_cs.player_num)
        print(f"connected is player {stringp}")
        p = createMessage(stringp)
        decodedP = int(p.decode('utf-8')[-1])
        _cs.socket.send(p)
        while _cs.is_active:
            try:
                # data received from client
                payload: str = receive_message(_cs.socket)
                if payload is None:
                    # slow down the next STREAM SOCKET read
                    time.sleep(1)
                    continue
                if VERBOSE:
                    log(f"received message payload [{payload}] from Player {decodedP}")
                with self.games[_game_id].game_mutex:
                    self.handle_client_msg(_cs, decodedP, _game_id, payload)
            except Exception as e:
                log("unknown error in client handling thread", e)
                # %%
                break

        current_game = self.games[_game_id]
        players_map = dict(current_game.get_players_map())
        if players_map.pop(decodedP):
            log(f"Removed {decodedP} from game's player_map")

        if decodedP == current_game.currentPlayer:
            log(f"closing current player {stringp} connection.")
            if len(players_map) > 0:
                _p: Player = random.choice(current_game.getPlayers())
                current_game.setPlayer(_p.number)
                current_game.setReady(_p.number)
                self.games[_game_id] = current_game
        else:
            log(f"closing client {stringp} connection.")

        self.number_of_usr -= 1
        # connection closed
        _cs.socket.close()

    def cleanup_thread(self):
        while not self.cleanup_interval.is_set():
            curr_ts = datetime.now()
            i = len(self.client_sockets_list) - 1
            while i >= 0:
                log(f"i = {i} and cslist = {len(self.client_sockets_list)}") if VERBOSE else None
                _cs = self.client_sockets_list[i]
                # if we miss 5 heartbeats in a row, time to close that socket
                x = (curr_ts - _cs.last_hb_received).total_seconds()
                y = (HEARTBEAT_INTERVAL_SECS * 2.0)
                if x > y:
                    log(f"Cleaning up player {_cs.player_num} socket")
                    stale = self.client_sockets_list.pop(i)
                    stale.mark_inactive()
                i -= 1
            self.cleanup_interval.wait(HEARTBEAT_INTERVAL_SECS)

    def handle_client_msg(self, _cs: ClientSocket, decoded_p: int,
                          _game_id: int,
                          payload: str):
        # if _game_id in games:
        current_game = self.games[_game_id]
        n = len(current_game.get_players_map().keys())
        # if bool(payload) is not False:
        (msg_enum, data) = payload.split(':')
        log(f"client request: {msg_enum}") if msg_enum not in ClientMsgReq.HeartBeat.msg else None
        client_req: ClientMsgReq = ClientMsgReq.parse_msg_string(msg_enum + ':')
        # %% set player ready
        if ClientMsgReq.HeartBeat == client_req:
            log("sending heartbeat response") if VERBOSE else None
            _cs.socket.sendall(createMessage(ClientMsgReq.HeartBeat.msg))
            _cs.set_last_active_ts()
            return
        elif ClientMsgReq.Start == client_req:
            log("player wants to start game ")
            # sets player ready
            current_game.getPlayer(decoded_p).set_start()
            # %%  check if all connected are ready
            readyMessage = ""
            for player in current_game.getPlayers():
                if player.start is False:
                    readyMessage += f" {player.number} not ready "
            if readyMessage:
                current_game.setServerMessage(
                    f"Not all players are ready. status {current_game.isReady()}")
            # %% sets leader
            else:
                _p: Player = random.choice(current_game.getPlayers())
                current_game.setPlayer(_p.number)
                current_game.setReady(_p.number)
                self.games[_game_id] = current_game
                current_game.setServerMessage(
                    "game ready to start ")
            # %%

        elif ClientMsgReq.Name == client_req:
            client_name = data
            current_game.getPlayer(decoded_p).name = client_name
            log(current_game.getPlayer(decoded_p).name)
            current_game.setServerMessage("player changed name")
        elif ClientMsgReq.Dice == client_req:
            diceValue = data
            diceValue = int(diceValue)
            log(f"diceValue is {diceValue}")
            if current_game.bag.get_remaining_tiles() < (
                    diceValue * n):
                log("no more bags")
                return
            else:
                # %% we have enough, are racks initialized?
                # giving racks their bag and dice values
                for player in current_game.get_players_map():
                    try:
                        current_game.getPlayer(player).rack.clear_rack()
                    except Exception as e:
                        log("clear rack failed", e)
                current_game.setRolled()
                current_game.setRacks(diceValue)
                current_game.setServerMessage(ClientResp.Racks_Ready.msg)
                log("handed racks to all")
                self.games[_game_id] = current_game
                for player in current_game.getPlayers():
                    try:
                        log(player.get_rack_str())
                        log(player.get_temp_str())
                    except Exception as e:
                        log("rack to str failed", e)
        # %% get
        elif ClientMsgReq.Get == client_req:
            log("[GET]")
        # %%
        elif ClientMsgReq.Buy == client_req:
            try:
                current_game.getPlayer(decoded_p).buy_word()
                current_game.setServerMessage(f"{ClientResp.Bought.msg} Player {decoded_p}")
            except Exception as e:
                log("buy failed", e)
        # %%
        elif ClientMsgReq.Cancel_Buy == client_req:
            try:
                current_game.getPlayer(decoded_p).cancel_buy(current_game.bag)
                current_game.setServerMessage(f"{ClientResp.Buy_Cancelled.msg} Player {decoded_p}")
            except Exception as e:
                log("buy cancellation failed", e)
        # %%
        elif ClientMsgReq.Sell == client_req:
            try:
                word = data
                _player = current_game.getPlayer(decoded_p)
                _player.sell(word, self.word_dict_csv)
                if _player.sell_check:
                    current_game.setServerMessage(f"{ClientResp.Sold.msg} {word} Player {decoded_p}")
                else:
                    current_game.setServerMessage(f"{ClientResp.Sell_Failed.msg} {word} Player {decoded_p}")
            except Exception as e:
                log("sell failed", e)
        # %%
        elif ClientMsgReq.Is_Done == client_req:
            round_enquiry = int(data)
            assert round_enquiry <= current_game.turn
            if round_enquiry == current_game.turn:
                readyOrNot = current_game.checkReady()
                if not readyOrNot:
                    msg = ClientResp.Done.msg + f" round: {current_game.turn}"
                    current_game.nextTurn()
                    current_game.setServerMessage(msg + f" curPlayer {current_game.currentPlayer}")
                else:
                    line = ",".join([name for name in readyOrNot])
                    line += " is " + ClientResp.Not_Ready.msg + " in round " + str(current_game.turn)
                    current_game.setServerMessage(line)
            elif round_enquiry < current_game.turn:
                current_game.setServerMessage(ClientResp.Done.msg + f" prev round: {round_enquiry}")
        # %%
        elif ClientMsgReq.Played == client_req:
            current_game.getPlayer(decoded_p).played = True
            current_game.setServerMessage(f"{ClientResp.Played.msg} Player {decoded_p}")

        self.games[_game_id] = current_game
        serverMessage = current_game.getServerMessage()
        log(f"serverMessage: {serverMessage} ")
        _cs.socket.sendall(createPickle(current_game))
        _cs.set_last_active_ts()


if __name__ == '__main__':
    s = Server()
    s.main()
