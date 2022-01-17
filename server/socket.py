from datetime import datetime
from socket import socket

from common.game import Player


class ClientSocket:
    def __init__(self, c_soc: socket, client_address):
        self.socket = c_soc
        self.c_addr = client_address
        self.last_hb_received = datetime.now()
        self.is_active = True
        self.player = None
        self.thread_name: str = ""

    def __repr__(self):
        return f"{self.player.game.game_id}-{self.player.name}-{self.player.number}"

    def post_handshake(self, g_id: int, player: Player):
        assert player.game.game_id == g_id
        self.player = player
        self.thread_name = f"{self.player.name}-{self.player.number}-{self.player.game.game_id}"

    def set_last_active_ts(self):
        self.last_hb_received = datetime.now()

    def mark_inactive(self):
        self.is_active = False

    def close(self, threads_list):
        # connection closed
        self.socket.close()
        for i in range(len(threads_list)):
            if threads_list[i].name == self.thread_name:
                threads_list.pop(i)
                break
