import random

import pygame
import thorpy

from gui.button import TextButton, RadioButton
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
        button_features = (5, 1.5, Colors.DARK_GRAY)
        # self.backtome = TextButton(h_margin_cells + 1,
        #                            v_margin_cells + 1, *button_features, " Return ",
        #                            Colors.ORANGE)
        equal_parts = width_cells // 4
        button_h_pos = equal_parts * 1.7
        button_v_pos = self.v_margin_cells - 5
        controls = [[(" Roll ", -9, 1), (" Cancel ", -5 + 4, 1)],
                    [("Create", -9, 3), (" Chat ", -5, 3)]
                    ]

        self.help_button = TextButton(self.h_margin_cells + button_h_pos,
                                      button_v_pos,
                                      *button_features, controls[0][0][0])

        self.remove_button = TextButton(self.h_margin_cells + (button_h_pos * 1.4),
                                        button_v_pos,
                                        *button_features, controls[0][1][0])

        self.option_button = RadioButton(self.h_margin_cells + (button_h_pos * 1.4),
                                         button_v_pos - 1.5,
                                         2, 4.3, on_display=False)
        self.option_button.add_option("2")
        self.option_button.add_option("3")
        self.option_button.add_option("4")
        self.option_button.add_option("5")

        # self.createbutton = TextButton(self.xmargin() + controls[1][0][1],
        #                                self.v_margin_cells + controls[1][0][2],
        #                                *button_features, controls[1][0][0])
        #
        # self.chatbutton = TextButton(self.xmargin() + controls[1][1][1],
        #                              self.v_margin_cells + controls[1][1][2],
        #                              *button_features, controls[1][1][0])

        self.dice: Dice = None
        self.__enable_dice_rolling = False
        self.__enable_buy = False
        self.__enable_sell = False
        self.last_rolled_dice_no = -1

    def refresh_dims(self):
        super().refresh_dims()
        # self.backtome.refresh_dims()

    def friendly_chat(self):
        pass

    def choose_dice(self):
        dvals = thorpy.DropDownListLauncher("Choose Dice", titles=[i for i in range(2, 5)])
        dvals.surface = self.game.surface
        dvals.blit()
        return dvals.get_value()

    def all_chat(self):
        pass

    def draw(self, win):
        pygame.draw.rect(win, (0, 0, 0), (self.x, self.y, self.width, self.height), self.BORDER_THICKNESS)
        self.option_button.draw(win)
        self.help_button.draw(win)
        # self.backtome.draw(win)
        self.remove_button.draw(win)
        # self.createbutton.draw(win)
        # self.chatbutton.draw(win)
        self.dice.draw() if self.dice else None

    def button_events(self):
        """
        handle all button press events here
        :return: None
        """
        mouse = pygame.mouse.get_pos()
        if self.option_button.on_display:
            self.option_button.click(*mouse)
            if self.help_button.click(*mouse):
                self.hide_input_prompt()

            # don't allow click anywhere else
            return

        if self.__enable_dice_rolling and self.help_button.click(*mouse):
            # choices = [("Choose Dice ", self.choose_dice()), ("cancel", None)]
            # thorpy.launch_blocking_choices("Help!\n",
            #                                choices)
            if not self.dice:
                self.dice = Dice(self.game, 200, 200, 100, 0.2)
                self.dice.draw()
                self.dice.roll(self.rand.randint(5, 15))
                return

        if self.__enable_buy:
            if self.help_button.click(*mouse):
                self.__enable_buy = False
                self.game.game_status = GameStatus.BUY
                self.revert_to_orig()
                return
            elif self.remove_button.click(*mouse):
                self.__enable_buy = False
                self.game.game_status = GameStatus.CANCEL_BUY
                self.revert_to_orig()
                return

        if self.__enable_sell:
            if self.help_button.click(*mouse):
                self.__enable_sell = False
                self.game.game_status = GameStatus.SELL
                self.revert_to_orig()
                return
            elif self.remove_button.click(*mouse):
                self.__enable_sell = False
                self.game.game_status = GameStatus.CANCEL_SELL
                self.revert_to_orig()
                return

        # if self.backtome.click(*mouse):
        #     self.game.myrack.returntome(self.game.tileList)
        if self.remove_button.click(*mouse):
            self.game.tileList.empty()
        # if self.createbutton.click(*mouse):
        #     self.game.inventory.get_word()
        # if self.chatbutton.click(*mouse):
        #     choices = [("All", print("hi")), ("Friendly", print("friend")), ("Cancel", None)]
        #     thorpy.launch_blocking_choices("Chat!\n",
        #                                    choices)

    def roll_dice(self):
        if self.dice:
            if self.dice.continue_rolling():
                return
            dice_value = self.dice.get_rolled_dice_no()
            msg = "Dice Rolled to: " + str(dice_value)
            self.game.top_bar.client_msgs.add_msg(msg)
            if dice_value in [1, 6]:
                self.prompt_input()
                return

            self.handle_rolled_dice(dice_value)

    def handle_rolled_dice(self, dice_value: int):
        self.last_rolled_dice_no = dice_value
        self.__enable_dice_rolling = False
        self.dice = None
        self.game.game_status = GameStatus.DICE_ROLL_COMPLETE
        self.revert_to_orig()

    def prompt_input(self):
        self.game.top_bar.client_msgs.add_msg("Your Choice. Enter between 2 to 5")
        self.help_button.set_text(" Choose ")
        self.remove_button.hide()
        self.option_button.show()
        self.game.game_status = GameStatus.PROMPT_DICE_INPUT
        # enable input field & validate
        # return random.randint(2, 5)

    def hide_input_prompt(self):
        user_chosen_dice_value = self.option_button.get_chosen_option_value() + 2
        msg = "Chosen dice value: " + str(user_chosen_dice_value)
        self.game.top_bar.client_msgs.add_msg(msg, Colors.RED)
        self.handle_rolled_dice(user_chosen_dice_value)
        self.help_button.set_text(" Help ")
        self.remove_button.show()
        self.option_button.hide()

    def enable_dice_rolling(self):
        self.last_rolled_dice_no = -2
        self.__enable_dice_rolling = True
        self.help_button.set_text(" ROLL ")
        self.help_button.set_color(Colors.GREEN)

    def revert_to_orig(self):
        self.help_button.set_text("  Help ")
        self.help_button.set_color(Colors.DARK_GRAY)
        self.remove_button.set_text(" Remove ")
        self.remove_button.set_color(Colors.DARK_GRAY)

    def enable_buy(self):
        self.__enable_buy = True
        self.help_button.set_text(" BUY ")
        self.help_button.set_color(Colors.GREEN)
        self.remove_button.set_text(" CANCEL ")
        self.remove_button.set_color(Colors.GREEN)

    def enable_sell(self):
        self.__enable_sell = True
        self.help_button.set_text(" SELL ")
        self.help_button.set_color(Colors.GREEN)
        self.remove_button.set_text(" CANCEL ")
        self.remove_button.set_color(Colors.GREEN)
