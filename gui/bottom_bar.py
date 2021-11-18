import random

import pygame
import thorpy

from gui.button import TextButton
from gui.dice import Dice
from gui.display import Display
from common.gameconstants import *


class BottomBar(Display):
    rand = random  # uniform randomness requires long living objects

    def __init__(self, h_margin_cells, v_margin_cells, width_cells, height_cells, game):
        super(BottomBar, self).__init__(h_margin_cells, v_margin_cells, width_cells, height_cells)
        w, h = Display.dims()
        # self.WIDTH = 660 / 800 * w
        # self.HEIGHT = 125 / 600 * h
        self.BORDER_THICKNESS = 5
        from gui.base import GameUI
        self.game: GameUI = game
        button_features = (3.5, 1.5, Colors.DARK_GRAY)
        self.backtome = TextButton(h_margin_cells + 1,
                                   v_margin_cells + 1, *button_features, " Return ",
                                   Colors.ORANGE)
        controls = [[(" Help ", -9, 1), (" Remove ", -5, 1)],
                    [("Create", -9, 3), (" Chat ", -5, 3)]
                    ]

        self.help_button = TextButton(self.xmargin() + controls[0][0][1],
                                      self.v_margin_cells + controls[0][0][2],
                                      *button_features, controls[0][0][0])

        self.removebutton = TextButton(self.xmargin() + controls[0][1][1],
                                       self.v_margin_cells + controls[0][1][2],
                                       *button_features, controls[0][1][0])

        self.createbutton = TextButton(self.xmargin() + controls[1][0][1],
                                       self.v_margin_cells + controls[1][0][2],
                                       *button_features, controls[1][0][0])

        self.chatbutton = TextButton(self.xmargin() + controls[1][1][1],
                                     self.v_margin_cells + controls[1][1][2],
                                     *button_features, controls[1][1][0])

        self.dice: Dice = None
        self.__enable_dice_rolling = False
        self.last_rolled_dice_no = -1

    def refresh_dims(self):
        super().refresh_dims()
        self.backtome.refresh_dims()

    def friendly_chat(self):
        pass

    def choose_dice(self):
        dvals = thorpy.DropDownListLauncher("Choose Dice", titles=[i for i in range(2, 5)])
        dvals.surface = self.game.surface
        dvals.blit()

    def all_chat(self):
        pass

    def draw(self, win):
        pygame.draw.rect(win, (0, 0, 0), (self.x, self.y, self.width, self.height), self.BORDER_THICKNESS)
        self.help_button.draw(win)
        self.backtome.draw(win)
        self.removebutton.draw(win)
        self.createbutton.draw(win)
        self.chatbutton.draw(win)
        self.dice.draw() if self.dice else None

    def button_events(self):
        """
        handle all button press events here
        :return: None
        """
        mouse = pygame.mouse.get_pos()
        if self.__enable_dice_rolling and self.help_button.click(*mouse):
            # choices = [("Choose Dice ", self.choose_dice()), ("cancel", None)]
            # thorpy.launch_blocking_choices("Help!\n",
            #                                choices)
            if not self.dice:
                self.dice = Dice(self.game, 200, 200, 100, 0.2)
                self.dice.draw()
                self.dice.roll(self.rand.randint(5, 15))
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

    def roll_dice(self):
        if self.dice:
            self.dice.continue_rolling()
            if not self.dice.is_dice_rolling():
                diceValue = self.dice.get_rolled_dice_no()
                self.game.top_bar.client_msgs.add_msg("Dice Rolled to: "
                                                      + str(diceValue))
                if diceValue not in [2, 3, 4, 5]:
                    diceValue = self.prompt_input()
                self.last_rolled_dice_no = diceValue
                self.disable_dice_rolling()

    def prompt_input(self):
        self.game.top_bar.client_msgs.add_msg("Your Choice. Enter between 2 to 5")
        # enable input field & validate
        return random.randint(2, 5)

    def enable_dice_rolling(self):
        self.last_rolled_dice_no = -2
        self.__enable_dice_rolling = True
        self.help_button.set_text(" ROLL ")
        self.help_button.set_color(Colors.GREEN)

    def disable_dice_rolling(self):
        self.__enable_dice_rolling = False
        self.dice = None
        self.help_button.set_text("  Help ")
        self.help_button.set_color(Colors.DARK_GRAY)
        self.game.game_status = GameStatus.DICE_ROLL_COMPLETE
