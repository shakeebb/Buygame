from datetime import datetime
from socket import socket

from common.game import Player


class ClientSocket:
    def __init__(self, c_soc: socket):
        self.socket = c_soc
        self.last_hb_received = datetime.now()
        self.is_active = True
        self.player = None
        self.thread_name: str = ""

    def __repr__(self):
        return f"{self.player.game.id}-{self.player.name}-{self.player.number}"

    def post_handshake(self, g_id: int, player: Player):
        assert player.game.id == g_id
        self.player = player
        self.thread_name = f"{self.player.name}-{self.player.number}-{self.player.game.id}"

    def set_last_active_ts(self):
        self.last_hb_received = datetime.now()

    def mark_inactive(self):
        self.is_active = False
