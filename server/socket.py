from datetime import datetime
from socket import socket


class ClientSocket:
    def __init__(self, c_soc: socket, c_num: int):
        self.socket = c_soc
        self.player_num = c_num
        self.last_hb_received = datetime.now()
        self.is_active = True

    def set_last_active_ts(self):
        self.last_hb_received = datetime.now()

    def mark_inactive(self):
        self.is_active = False
