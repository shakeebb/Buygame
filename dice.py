"""
A dice that simulates rolling from 1-6 and its upto the
consumer to take actions accordingly.
"""
import random
import time

import pygame


class Dice:
    spot_color = (0, 0, 0)
    d: pygame.Rect = None
    roll_no = 0
    rand = random

    def __init__(self, win: pygame.Surface, x, y, size, refresh_interval):
        """
        Dice class that rolls and returns random number between 1 - 6.

        x: starting 'x' position on the surface
        y: starting 'y' position on the surface
        size: dice size (side of a square)
        refresh_interval: sleep wait time between dice rolls.
        """
        self.win = win
        self.x = x
        self.y = y
        self.size = size
        self.interval = refresh_interval

        # calculated fields
        self.dots_sz = size // 10
        self.mid = size // 2  # mid-point of the dice
        self.left = self.top = self.size // 4
        self.right = self.bottom = self.size - self.left

    def draw(self):
        self.d = pygame.draw.rect(self.win, (255, 255, 255),
                                  (self.x, self.y, self.size, self.size))
        if self.roll_no > 0:
            self.__spotify_dice(self.roll_no)

    def clear(self):
        self.roll_no = 0

    def __draw_spot(self, d1, d2):
        pygame.draw.circle(self.win, self.spot_color, (self.x + d1, self.y + d2), self.dots_sz)

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

    def roll(self, num_iter):
        for i in range(num_iter):
            self.roll_no = random.randint(1, 6)
            self.draw()
            self.__spotify_dice(self.roll_no)
            time.sleep(self.interval)
            pygame.display.update()
        return self.roll_no
