# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 12:19:27 2021

@author: Boss
"""

import pickle
import socket
import time
from threading import Thread, Event, RLock

from common.gameconstants import *
from common.logger import log


def createMessage(message: str):
    try:
        if message is not None:
            message = message.encode('utf-8')

        return message
        # creates message ready for socket 
        # needs message, HEADER_LENGTH
        # returns message ready for socket 
    except Exception as e:
        log(e)


def createPickle(aPickle):
    aPickled = pickle.dumps(aPickle)
    aPickled = bytes(aPickled)
    return aPickled


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
        log(e)
        return False


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(MSG_HEADER_LENGTH)
        if not len(message_header):
            return False

        message_length = int(message_header.decode('utf-8').strip())
        return client_socket.recv(message_length).decode('utf-8')
    except Exception as e:
        log(e)
        return False


class Network:
    def __init__(self):
        log("creating client socket")
        self.client: socket = self.create_client_socket()
        self.is_connected = False
        self.server = "localhost"
        self.port = 1234
        self.addr = (self.server, self.port)
        self.con_mutex = RLock()
        self.hb_thread = Thread(target=self.heartbeat, name="heartbeat", daemon=True)
        self.hb_event = Event()

        self.p = int(self.connect())

        self.hb_thread.start()
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
            return soc
        except socket.error as se:
            log(se)
            return None

    def getP(self):
        return self.p

    def heartbeat(self):
        while not self.hb_event.is_set():
            with self.con_mutex:
                try:
                    if not self.is_connected:
                        log("HB realised disconnection... reconnecting")
                        self.reconnect()

                    # if still not connected, loop
                    if not self.is_connected:
                        self.hb_event.wait(HEARTBEAT_INTERVAL_SECS)
                        continue
                    if VERBOSE:
                        log("HB sending")
                    self.client.send(createMessage(ClientMsg.HeartBeat.msg))
                    resp = receive_message(self.client)
                    if VERBOSE:
                        log("HB received " + str(resp))
                    if str(resp) == ClientMsg.HeartBeat.msg:
                        self.is_connected = True
                    elif bool(resp) is False:
                        self.is_connected = False
                except Exception as e:
                    log(e)
                    self.is_connected = False
            self.hb_event.wait(HEARTBEAT_INTERVAL_SECS)

    def reconnect(self):
        with self.con_mutex:
            try:
                log("creating fresh client socket")
                self.client = self.create_client_socket(True)
                self.client.connect(self.addr)
                self.is_connected = True
                log("client socket created")
            except Exception as e:
                log(e)
                self.is_connected = False

    def connect(self):
        with self.con_mutex:
            try:
                log("time to connect")
                self.client.connect(self.addr)
                log("connected successful")
                time.sleep(1)
                myP = receive_message(self.client)
                myNumber = int(myP)
                self.is_connected = True
                return myNumber
            except Exception as e:
                log(e)
                log("failed to connect")
                self.is_connected = False
                return 0

    def disconnect(self):
        self.hb_event.set()
        self.hb_thread.join()

    def send(self, data: str) -> object:
        if not self.is_connected:
            log("Automatically Reconnecting")
            self.reconnect()

        while True:
            with self.con_mutex:
                try:
                    # print("trying to send data to server")
                    self.client.send(createMessage(data))
                    self.is_connected = True
                    # print(f"{data} sent")
                    time.sleep(1)
                    data = receive_pickle(self.client)
                    time.sleep(1)
                    if bool(data) is not False:
                        # print(f"[game] {data}")
                        return data
                    else:
                        return None
                except socket.error as e:
                    log(e)
                    self.is_connected = False
                    return None

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
