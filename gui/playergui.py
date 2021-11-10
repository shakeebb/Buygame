"""
Represents the player(s) in each game
"""
from common.gameconstants import *


class PlayerGUI(object):
    def __init__(self, name: str, number: str):
        self.name = name[0:MAX_NAME_LENGTH]
        self.number = number
        self.score = 200

    def update_score(self, x):
        self.score += x

    def get_score(self):
        return self.score

    def get_name(self):
        return self.name
