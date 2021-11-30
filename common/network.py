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
        log("create message failed", e)


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
        message = client_socket.recv(message_length, socket.MSG_WAITALL)
        # print("message", message)
        unpickled = pickle.loads(message)
        # print("unpickled", unpickled)
        return unpickled
    except Exception as e:
        log("deserialization failed", e)
        return False


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(MSG_HEADER_LENGTH, socket.MSG_WAITALL)
        if not len(message_header):
            return False

        message_length = int(message_header.decode('utf-8').strip())
        return client_socket.recv(message_length, socket.MSG_WAITALL).decode('utf-8')
    except Exception as e:
        log("receive message failed with", e)
        return False


class Network:
    def __init__(self):
        log("creating client socket")
        self.client: socket = self.create_client_socket()
        self.is_connected = False
        # self.server = "localhost"
        # self.port = 1234
        self.server = "18.219.32.107"
        self.port = 58092
        self.addr = (self.server, self.port)
        self.con_mutex = RLock()
        self.p = int(self.connect())
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
                self.client.sendall(createMessage(ClientMsgReq.HeartBeat.msg))
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
        with self.con_mutex:
            try:
                log("creating fresh client socket")
                self.client = self.create_client_socket(True)
                self.client.connect(self.addr)
                self.is_connected = True
                log("client socket created")
            except Exception as e:
                log("reconnect failed with", e)
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
                log("failed to connect", e)
                self.is_connected = False
                raise e

    def send(self, data: str) -> object:
        sleepTime = 1
        while True:
            if not self.is_connected:
                log("Automatically Reconnecting")
                self.reconnect()

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
                    log("send failed with", e)
                    self.is_connected = False
                    time.sleep(sleepTime)
                    if sleepTime < MAX_RECONNECT_TIME:
                        sleepTime *= 2
                        continue
                    else:
                        raise e

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
