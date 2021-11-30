"""
A dice that simulates rolling from 1-6 and its upto the
consumer to take actions accordingly.
"""
import random

import pygame

from common.gameconstants import *
from common.logger import log


class Dice:
    spot_color = (0, 0, 0)
    ROLL_DICE_EVENT = pygame.event.Event(EV_DICE_ROLL)
    rand = random  # uniform random requires long living objects

    def __init__(self, game, x, y, size, refresh_interval):
        """
        Dice class that rolls and returns random number between 1 - 6.

        x: starting 'x' position on the surface
        y: starting 'y' position on the surface
        size: dice size (side of a square)
        refresh_interval: sleep wait time between dice rolls.
        """
        self.game = game
        self.x = x
        self.y = y
        self.size = size
        self.interval = refresh_interval

        # calculated fields
        self.dots_sz = size // 10
        self.mid = size // 2  # mid-point of the dice
        self.left = self.top = self.size // 4
        self.right = self.bottom = self.size - self.left

        # init member vars
        self.dice_rolled = False
        self.rolled_no = 0
        self.roll_number_of_iters = 0
        self.d: pygame.Rect = None

    def draw(self):
        self.d = pygame.draw.rect(self.game.surface, Colors.WHITE.value,
                                  (self.x, self.y, self.size, self.size))
        self.d = pygame.draw.rect(self.game.surface, Colors.BLACK.value,
                                  (self.x, self.y, self.size, self.size), 1)
        if self.rolled_no > 0:
            self.__spotify_dice(self.rolled_no)

    def clear(self):
        self.dice_rolled = False
        self.rolled_no = 0
        self.roll_number_of_iters = 0

    def __draw_spot(self, d1, d2):
        pygame.draw.circle(self.game.surface, self.spot_color, (self.x + d1, self.y + d2), self.dots_sz)

    def __spotify_dice(self, r):
        if r % 2 == 1:  # for 1, 3, 5 draw the center spot
            self.__draw_spot(self.mid, self.mid)
        if r == 2 or r == 3 or r == 4 or r == 5 or r == 6:  # just draw the diagonals
            self.__draw_spot(self.left, self.bottom)
            self.__draw_spot(self.right, self.top)
        if r == 4 or r == 5 or r == 6:
            self.__draw_spot(self.left, self.top)
            self.__draw_spot(self.right, self.bottom)
        if r == 6:
            self.__draw_spot(self.left, self.mid)
            self.__draw_spot(self.right, self.mid)

    def continue_rolling(self):
        if self.is_dice_rolling():
            self.rolled_no = self.rand.randint(1, 6)
            log("Rolling for " + str(self.roll_number_of_iters) + " rolled to " + str(self.rolled_no)) \
                if VERBOSE else None
            self.dice_rolled = False
        else:
            self.dice_rolled = True

        self.draw()
        self.roll_number_of_iters -= 1
        if not self.is_dice_rolling():
            log(f"Cancelling the timer... {self.dice_rolled}") if VERBOSE else None
            pygame.time.set_timer(self.ROLL_DICE_EVENT, 0)  # disable timer
            # just put one extra event, to handle post dice_rolled.
            pygame.event.post(self.ROLL_DICE_EVENT) if not self.dice_rolled else None
        return not self.dice_rolled

    def roll(self, num_iter):
        if self.is_dice_rolling():
            return
        self.roll_number_of_iters = num_iter
        pygame.time.set_timer(self.ROLL_DICE_EVENT, 200)  # every 100ms
        # self.game.chat.update_chat("Dice rolling")

    def is_dice_rolling(self):
        return self.roll_number_of_iters > 0

    def get_rolled_dice_no(self):
        return self.rolled_no
