import time

import pygame
import thorpy

from button import TextButton
from dice import Dice


class BottomBar:
    COLORS = {
        0: (255, 255, 255),
        1: (0, 0, 0),
        2: (255, 0, 0),
        3: (0, 255, 0),
        4: (0, 0, 255),
        5: (255, 255, 0),
        6: (255, 140, 0),
        7: (165, 42, 42),
        8: (128, 0, 128)
    }
    dice: Dice = None

    def __init__(self, x, y, game):
        self.x = x
        self.y = y
        self.WIDTH = 660 / 800 * game.WIDTH
        self.HEIGHT = 125 / 600 * game.HEIGHT
        self.BORDER_THICKNESS = 5
        self.game = game
        self.help_button = TextButton(self.x + 550 / 800 * game.WIDTH,
                                      self.y + 25 / 600 * game.HEIGHT, 80, 50, (128, 128, 128), "Help")
        self.backtome = TextButton(self.x + 10 / 800 * game.WIDTH,
                                   self.y + 25 / 600 * game.HEIGHT, 80, 50, (128, 128, 128), "Return")
        self.removebutton = TextButton(self.x + 600 / 800 * game.WIDTH,
                                       self.y + 25 / 600 * game.HEIGHT, 80, 50, (128, 128, 128), "Remove")
        self.createbutton = TextButton(self.x + 600 / 800 * game.WIDTH,
                                       self.y + 75 / 600 * game.HEIGHT, 80, 50, (128, 128, 128), "Create")
        self.chatbutton = TextButton(self.x + 550 / 800 * game.WIDTH,
                                     self.y + 75 / 600 * game.HEIGHT, 80, 50, (128, 128, 128), "Chat")

    def friendly_chat():
        pass

    def choose_dice(self):
        dvals = thorpy.DropDownListLauncher("Choose Dice", titles=[i for i in range(2, 5)])
        dvals.surface = self.game.win
        dvals.blit()

    def all_chat():
        pass

    def draw(self, win):
        pygame.draw.rect(win, (0, 0, 0), (self.x, self.y, self.WIDTH, self.HEIGHT), self.BORDER_THICKNESS)
        self.help_button.draw(win)
        self.backtome.draw(win)
        self.removebutton.draw(win)
        self.createbutton.draw(win)
        self.chatbutton.draw(win)
        if self.dice is not None:
            self.dice.draw()

    def button_events(self):
        """
        handle all button press events here
        :return: None
        """
        mouse = pygame.mouse.get_pos()
        if self.dice is not None:
            self.dice = None

        if self.help_button.click(*mouse):
            # choices = [("Choose Dice ", self.choose_dice()), ("cancel", None)]
            # thorpy.launch_blocking_choices("Help!\n",
            #                                choices)
            self.dice = Dice(self.game.win, 200, 200, 100, 0.2)
            self.dice.draw()
            roll = self.dice.roll(10)
            self.game.chat.update_chat("Help Message " + str(roll))
        if self.backtome.click(*mouse):
            self.game.myrack.returntome(self.game.tileList)
        if self.removebutton.click(*mouse):
            self.game.tileList.empty()
        if self.createbutton.click(*mouse):
            self.game.inventory.createWord()
        if self.chatbutton.click(*mouse):
            choices = [("All", print("hi")), ("Friendly", print("friend")), ("Cancel", None)]
            thorpy.launch_blocking_choices("Chat!\n",
                                           choices)
