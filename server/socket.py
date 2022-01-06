from datetime import datetime
from socket import socket


class ClientSocket:
    def __init__(self, c_soc: socket, g_id: int, c_num: int):
        self.socket = c_soc
        self.last_hb_received = datetime.now()
        self.player_num = c_num
        self.game_id = g_id
        self.is_active = True
        self.thread_name = f"client-{self.game_id}-{str(self.player_num)}"

    def set_last_active_ts(self):
        self.last_hb_received = datetime.now()

    def mark_inactive(self):
        self.is_active = False
