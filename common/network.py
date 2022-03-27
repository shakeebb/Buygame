# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 12:19:27 2021

@author: Boss
"""

import pickle
import socket
import time
from sys import platform
from threading import Thread, Event, RLock

from common.game import Game
from common.gameconstants import *
from common.logger import log


# def createMessage(message: str):
#     try:
#         if message is not None:
#             message = message.encode('utf-8')
#
#         return message
#         # creates message ready for socket
#         # needs message, HEADER_LENGTH
#         # returns message ready for socket
#     except Exception as e:
#         log("create message failed", e)
#
#
# def createPickle(aPickle):
#     aPickled = pickle.dumps(aPickle)
#     aPickled = bytes(aPickled)
#     return aPickled
from common.utils import receive_message, receive_pickle, serialize, ObjectType


class Network:
    def __init__(self, ip, port, session_id, player_name, socket_timeout):
        log(f"creating {player_name} client socket to {ip}:{port} with {session_id}")
        self.retries = MAX_RETRY
        self.socket_timeout = socket_timeout
        self.client: socket = self.create_client_socket()
        self.is_connected = False
        self.server = ip
        self.port = port
        self.session_id: str = session_id
        self.player_name = player_name
        self.addr = (self.server, int(self.port))
        self.con_mutex = RLock()
        log("done initialize")

    def create_client_socket(self, try_close_existing=False):
        try:
            if try_close_existing:
                try:
                    self.client.shutdown(1)
                    self.client.close()
                except socket.error:
                    pass
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            soc.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            if platform != "win32":
                soc.settimeout(self.socket_timeout)
            return soc
        except socket.error as se:
            log("client socket creation failed", se)
            return None

    def getP(self):
        return self.p

    def heartbeat(self):
        with self.con_mutex:
            try:
                if not self.is_connected:
                    log("HB realised disconnection... reconnecting")
                    self.reconnect()
                # if still not connected, return
                if not self.is_connected:
                    return
                if VERBOSE:
                    log("HB sending")
                self.client.sendall(serialize(ObjectType.MESSAGE, ClientMsgReq.HeartBeat.msg))
                resp = receive_message(self.client)
                if VERBOSE:
                    log("HB received " + str(resp))
                if str(resp) == ClientMsgReq.HeartBeat.msg:
                    self.is_connected = True
                elif bool(resp) is False:
                    self.is_connected = False
            except Exception as e:
                log("heartbeat failed with ", e)
                self.is_connected = False

    def reconnect(self):
        if self.is_connected:
            return True

        while self.retries > 0:
            log(f"Reconnecting {self.retries}")
            with self.con_mutex:
                try:
                    self.__connect(True)
                    log("client socket created")
                    self.retries = MAX_RETRY
                    return True
                except Exception as e:
                    if VERBOSE:
                        log("reconnect failed with", e)
                    self.is_connected = False
                    self.retries -= 1
                    if self.retries <= 0:
                        raise BrokenPipeError("network:reconnect exhausted", e)

    def connect(self) -> Game:
        with self.con_mutex:
            try:
                log(f"time to connect {self.addr}")
                return self.__connect(False)
            except Exception as e:
                log("failed to connect", e)
                self.is_connected = False
                raise

    def __connect(self, try_closing: bool) -> Game:
        self.client = self.create_client_socket(try_closing)
        try:
            self.client.connect(self.addr)
            self.is_connected = True
            if len(self.session_id) == 0:
                s_id = f"[{self.player_name}]"
            else:
                s_id = self.session_id
            _g = self.send(ClientMsgReq.SessionID.msg + s_id)
            assert _g is None or isinstance(_g, Game)
            game: Game = _g
            time.sleep(0.001)
            new_session_id = receive_message(self.client, block=True)
            if new_session_id is None:
                raise Exception(f"Could not connect to the server {self.server}")
            if len(new_session_id) > 0:
                self.session_id = new_session_id
                self.is_connected = True
            return game
        except Exception as e:
            if VERBOSE:
                log("Network:Connect exception: ", e)
            self.is_connected = False
            raise

    def send(self, data: str) -> object:
        sleepTime = 0.01
        while True:
            self.reconnect()

            with self.con_mutex:
                try:
                    # print("trying to send data to server")
                    payload = serialize(ObjectType.MESSAGE, data)
                    self.client.send(payload)
                    self.is_connected = True
                    # print(f"{data} sent")
                    time.sleep(0.01)
                    data = receive_pickle(self.client)
                    # time.sleep(1)
                    if bool(data) is not False:
                        # print(f"[game] {data}")
                        return data
                    else:
                        return None
                except socket.error as e:
                    log("send failed with", e)
                    self.is_connected = False
                    time.sleep(sleepTime)
                    if sleepTime < MAX_RECONNECT_TIME:
                        sleepTime *= 2
                        continue
                    else:
                        raise

    # def sendP(self, data):
    #     while True:
    #         try:
    #             # print("trying to send data to server")
    #             self.client.send(createPickle(data))
    #             log(f"{data} sent")
    #             time.sleep(2)
    #             data = receive_pickle(self.client)
    #             if data is not False:
    #                 log(f"[game] {data}")
    #                 return data
    #         except socket.error as e:
    #             log(e)
