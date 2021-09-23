# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 12:19:27 2021

@author: Boss
"""


import socket
import pickle
import time
HEADER_LENGTH = 2048
def createMessage(message):
    HEADER_LENGTH = 2048
    try:
        if message is not False:
            message = message.encode('utf-8')
        
        return message
        # creates message ready for socket 
        # needs message, HEADER_LENGTH
        # returns message ready for socket 
    except Exception as e:
        print(e)
def createPickle(aPickle):
    HEADER_LENGTH = 4096
    aPickled = pickle.dumps(aPickle)
    aPickled = bytes(aPickled)
    return aPickled
def receive_pickle(client_socket):
    try:
        HEADER_LENGTH = 4096
        message_header = client_socket.recv(HEADER_LENGTH)
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
def receive_message(client_socket):
    HEADER_LENGTH = 2048
    try:
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False

        message_length = int(message_header.decode('utf-8').strip())

        return client_socket.recv(message_length).decode('utf-8')

    except:
        return False
class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "localhost"
        self.port = 1234
        self.addr = (self.server, self.port)
        self.p = int(self.connect())
        print("done initialize")
        
    def getP(self):
        return self.p

    def connect(self):
        try:
            print("time to connect")
            self.client.connect(self.addr)
            print("connected successful")
            time.sleep(1)
            myP = receive_message(self.client)
            myNumber = int(myP)
            return myNumber
        except Exception as e:
            print(e)
            print("failed to connect")
            pass

    def send(self, data):
        while True:
            try:
                # print("trying to send data to server")    
                self.client.send(createMessage(data))
                # print(f"{data} sent")
                time.sleep(1)
                data = receive_pickle(self.client)
                time.sleep(1)
                if data != False:
                    # print(f"[game] {data}")
                    return data
            except socket.error as e:
                print(e)
    
    def sendP(self, data):
        while True:
            try:
                # print("trying to send data to server")
                self.client.send(createPickle(data))
                print(f"{data} sent")
                time.sleep(2)
                data = receive_pickle(self.client)
                if data != False:
                    print(f"[game] {data}")
                    return data
            except socket.error as e:
                print(e)
            