# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 13:40:58 2021

@author: Boss
"""
import datetime
import pickle
import socket
import os
# import thread module
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
GAMETILES = pd.read_csv(os.path.join(script_path, "tiles.csv"), index_col="LETTER")
GAMETILES
# bag = GAMETILES
WordDict = pd.read_json(os.path.join(script_path, 'words_dictionary.json'), typ='series').index

HEADER_LENGTH = 2048
IP = "localhost"
PORT = 1234
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# SO_REUSEADDR  is being set to 1(true), if program is restarted TCP socket we created can be used again
# without waiting for a for the socket to be fully closed.
# server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# binding socket and listening for connections
server_socket.bind((IP, PORT))
server_socket.listen(4)
print("server started.....")
nofw = 4
client_sockets_list: [ClientSocket] = []
clients = {}
number_of_usr = 0
waitingForGameToStart = True
games: Game = {}
gameId = 0


# %%

def createMessage(message):
    message = f"{len(message):<{MSG_HEADER_LENGTH}}".encode(
        'utf-8') + message.encode('utf-8')
    return message


def createPickle(aPickle):
    aPickled = pickle.dumps(aPickle)
    aPickled = bytes(f"{len(aPickled):<{SERIALIZE_HEADER_LENGTH}}".encode(
        'utf-8') + aPickled)
    return aPickled


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(MSG_HEADER_LENGTH)

        if not len(message_header):
            return False

        message = message_header.decode('utf-8').strip()

        return message

    except Exception as e:
        print(e)
        return False


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
    except:
        return False


# %%


def threaded(_cs: ClientSocket, _game_id):
    global number_of_usr
    # c is socket
    stringp = str(_cs.player_num)
    print(f"connected is player {stringp}")
    p = createMessage(stringp)
    _cs.socket.send(p)
    while _cs.is_active:
        try:
            # data received from client
            data = receive_message(_cs.socket)
            if data:
                print(f"received {data}")
                decodedP = int(p.decode('utf-8')[-1])
                print("[DATA From Player:]", decodedP)
                # if _game_id in games:
                currentgame = games[_game_id]
                n = len(currentgame.clients)
                if data is not False:

                    # %% set player ready
                    if ClientMsg.HeartBeat.msg == data:
                        if VERBOSE:
                            log("sending heartbeat response")
                        _cs.socket.sendall(createMessage(ClientMsg.HeartBeat.msg))
                        _cs.set_last_active_ts()
                        continue
                    elif data == "start":
                        log("player wants to start game ")
                        # sets player ready
                        currentgame.clients[decodedP].set_start()
                        # %%  check if all connected are ready
                        readyMessage = ""
                        for player in currentgame.getPlayers():
                            if player.start is False:
                                readyMessage += f" {player.number} not ready "
                        if readyMessage:
                            currentgame.setServerMessage(
                                "Not all players are ready ")
                        # %% sets leader
                        else:

                            playerIndex = random.randint(0, n - 1)
                            currentgame.setPlayer(playerIndex)
                            currentgame.setReady(playerIndex)
                            games[_game_id] = currentgame
                            currentgame.setServerMessage(
                                "game ready to start ")
                        # %%

                    elif ClientMsg.Name.msg in data:
                        client_name = data.split(' ')[1]
                        currentgame.clients[decodedP].name = client_name
                        log(currentgame.clients[decodedP].name)
                        currentgame.setServerMessage("player changed name")
                    elif ClientMsg.Dice.msg in data:
                        diceValue = data.split(' ')[1]
                        diceValue = int(diceValue)
                        log(f"diceValue is {diceValue}")
                        if currentgame.bag.get_remaining_tiles() < (
                                diceValue * n):
                            log("no more bags")
                            break
                        else:
                            # %% we have enough, are racks initialized?
                            # giving racks their bag and dice values
                            for player in currentgame.clients:
                                try:
                                    currentgame.clients[player].rack.clear_rack()
                                except Exception as e:
                                    log(e)
                            currentgame.setRolled()
                            currentgame.setRacks(diceValue)
                            currentgame.setServerMessage("Racks Ready")
                            log("handed racks to all")
                            games[_game_id] = currentgame
                            for player in currentgame.getPlayers():
                                try:
                                    log(player.get_rack_str())
                                    log(player.get_temp_str())
                                except Exception as e:
                                    log(e)
                    # %% get
                    elif "get" in data:
                        log("[GET]")
                    # %%
                    elif "buying" in data:
                        try:
                            currentgame.clients[decodedP].buy_word()
                            currentgame.setServerMessage("Purchased")
                        except Exception as e:
                            print(e)
                            print("cant buy ")
                    # %%
                    elif "Sold" in data:
                        word = data.split(" ")[1].strip()
                        currentgame.clients[decodedP].sell(word)
                        currentgame.setServerMessage("SOLD")
                    # %%
                    elif "Done" in data:
                        readyOrNot = currentgame.checkReady()
                        if not readyOrNot:
                            currentgame.nextTurn()
                            currentgame.setServerMessage("Done")
                        else:
                            line = ""
                            for name in readyOrNot:
                                line += name + " is not ready"
                            currentgame.setServerMessage(line)
                    # %%
                    elif "Played" in data:
                        currentgame.getPlayer(decodedP).played = True
                    games[_game_id] = currentgame
                    serverMessage = currentgame.getServerMessage()
                    log(f"serverMessage: {serverMessage} ")
                    _cs.socket.sendall(createPickle((currentgame)))
                    _cs.set_last_active_ts()
        except Exception as e:
            print(e)
            # %%
            break
    print("lost connection")
    number_of_usr -= 1
    # connection closed
    _cs.socket.close()


cleanup_interval = Event()


def cleanup_thread():
    while not cleanup_interval.is_set():
        curr_ts = datetime.now()
        i = len(client_sockets_list) - 1
        while i >= 0:
            print(f"i = {i} and cslist = {len(client_sockets_list)}")
            _cs = client_sockets_list[i]
            # if we miss 5 heartbeats in a row, time to close that socket
            x = (curr_ts - _cs.last_hb_received).total_seconds()
            y = (HEARTBEAT_INTERVAL_SECS * 2.0)
            if x > y:
                print(f"Cleaning up {cs.player_num}th player socket")
                stale = client_sockets_list.pop(i)
                stale.mark_inactive()
            i -= 1
        cleanup_interval.wait(HEARTBEAT_INTERVAL_SECS)


# Waiting for players to join lobby and to start game
while True:

    client_socket, client_address = server_socket.accept()
    # adding client socket to list of users
    print(f"[CONNECTION] {client_address} connected!")
    cs = ClientSocket(client_socket, len(client_sockets_list))
    client_sockets_list.append(cs)
    if number_of_usr == 0:
        print("Creating a new game....")
        games[gameId] = Game(gameId, GAMETILES)
        start_new_thread(cleanup_thread, ())
    print("creating player object...")
    # Giving player their own socket in dictionary 
    clients[number_of_usr] = Player(int(nofw), int(number_of_usr), games[gameId].getGameBag())
    # putting player in game
    print("player created")
    games[gameId].setClients(clients)
    print("setting clients to game \n sending game to client")
    # sending game to player 
    start_new_thread(threaded, (cs, gameId))
    print("game sent to client ")
    number_of_usr += 1
