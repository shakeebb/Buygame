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
        from gui.gameui import GameUI
        self.game: GameUI = game
        button_features = (5 * TILE_ADJ_MULTIPLIER, 1.5 * TILE_ADJ_MULTIPLIER, Colors.GREEN)
        # self.backtome = TextButton(h_margin_cells + 1,
        #                            v_margin_cells + 1, *button_features, " Return ",
        #                            Colors.ORANGE)
        equal_parts = width_cells // 4
        button_h_pos = equal_parts * 1.1
        button_v_pos = self.v_margin_cells - (5 * TILE_ADJ_MULTIPLIER)
        controls = [(" Roll ", -9, 1),
                    (" Discard ", -5 + 4, 1),
                    (" End Turn ", -5 + 8, 1),
                    ]

        self.action_button = TextButton(self.h_margin_cells + button_h_pos,
                                        button_v_pos,
                                        *button_features, controls[0][0],
                                        visual_effects=True)

        self.discard_button = TextButton(self.h_margin_cells + (button_h_pos * 1.6),
                                         button_v_pos,
                                         *button_features, controls[1][0],
                                         visual_effects=True)

        self.end_turn_button = TextButton(self.h_margin_cells + (button_h_pos * 2.2),
                                          button_v_pos,
                                          *button_features, controls[2][0],
                                          visual_effects=True)

        self.option_button = RadioButton(self.h_margin_cells + (button_h_pos * 1.6),
                                         button_v_pos - 1.5,
                                         2 * TILE_ADJ_MULTIPLIER, 4.3 * TILE_ADJ_MULTIPLIER,
                                         on_display=False)
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
        self.hide_all()

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
        self.action_button.draw(win)
        self.discard_button.draw(win)
        # self.backtome.draw(win)
        self.end_turn_button.draw(win)
        # self.createbutton.draw(win)
        # self.chatbutton.draw(win)
        self.dice.draw() if self.dice else None

    def foreach_controls(self, action, condition=None):
        for control in [self.action_button, self.discard_button, self.end_turn_button]:
            if condition is None or condition(control):
                action(control)

    def mouse_down(self):
        mouse = pygame.mouse.get_pos()
        self.foreach_controls(lambda c: c.mouse_down(),
                              lambda c: c.click(*mouse))

    def mouse_up(self):
        """
        handle all button press events here
        :return: None
        """
        mouse = pygame.mouse.get_pos()
        self.foreach_controls(lambda c: c.mouse_up())

        if self.option_button.on_display:
            self.option_button.click(*mouse)
            if self.action_button.click(*mouse):
                self.hide_input_prompt()

            # don't allow click anywhere else
            return

        if self.__enable_dice_rolling and self.action_button.click(*mouse):
            # choices = [("Choose Dice ", self.choose_dice()), ("cancel", None)]
            # thorpy.launch_blocking_choices("Help!\n",
            #                                choices)
            if not self.dice:
                self.dice = Dice(self.game,
                                 self.action_button.x - (4 * INIT_TILE_SIZE * TILE_ADJ_MULTIPLIER),
                                 self.action_button.y,
                                 100, 0.2)
                self.dice.draw()
                self.dice.roll(self.rand.randint(5, 15))
                return

        if self.__enable_buy:
            if self.action_button.click(*mouse):
                self.game.ui_game_status = GameUIStatus.BUY
                self.hide_all()
                return
            elif self.discard_button.click(*mouse):
                self.__enable_buy = False
                self.game.ui_game_status = GameUIStatus.SKIP_BUY
                self.hide_all()
                return

        if self.__enable_sell:
            if self.action_button.click(*mouse):
                self.game.ui_game_status = GameUIStatus.SELL
                self.hide_all()
                return
            elif self.discard_button.click(*mouse):
                self.game.ui_game_status = GameUIStatus.DISCARD_SELL
                self.hide_all()
                return
            elif self.end_turn_button.click(*mouse):
                self.game.ui_game_status = GameUIStatus.END_TURN
                return

        # if self.backtome.click(*mouse):
        #     self.game.myrack.returntome(self.game.tileList)
        if self.discard_button.click(*mouse):
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

    def prompt_input(self):
        self.game.top_bar.client_msgs.add_msg("Your Choice. Enter between 2 to 5")
        self.action_button.set_text(" Choose ")
        self.option_button.show()
        self.game.ui_game_status = GameUIStatus.PROMPT_DICE_INPUT
        # enable input field & validate
        # return random.randint(2, 5)

    def hide_input_prompt(self):
        user_chosen_dice_value = self.option_button.get_chosen_option_value() + 2
        msg = "Chosen dice value: " + str(user_chosen_dice_value)
        self.game.top_bar.client_msgs.add_msg(msg, Colors.RED)
        self.handle_rolled_dice(user_chosen_dice_value)
        self.hide_all()

    def handle_rolled_dice(self, dice_value: int):
        self.last_rolled_dice_no = dice_value
        self.__enable_dice_rolling = False
        self.dice = None
        self.game.ui_game_status = GameUIStatus.DICE_ROLL_COMPLETE
        self.hide_all()

    def enable_dice_rolling(self):
        self.last_rolled_dice_no = -2
        self.__enable_dice_rolling = True
        self.action_button.set_text(" ROLL ")
        self.action_button.show()
        self.action_button.enable()

    def show_buy(self, enabled=True):
        self.__enable_buy = True
        self.action_button.set_text(" BUY ")
        self.action_button.set_color(Colors.GREEN)
        self.discard_button.set_text(" SKIP ")
        self.discard_button.set_color(Colors.GREEN)
        self.action_button.show()
        self.discard_button.show()
        if enabled:
            self.enable_action()
        else:
            self.disable_action()

    def show_sell(self, enabled=False):
        self.__enable_sell = True
        self.action_button.set_text(" SELL ")
        self.action_button.set_color(Colors.GREEN)
        self.discard_button.set_text(" DISCARD ")
        self.discard_button.set_color(Colors.GREEN)
        self.action_button.show()
        self.discard_button.show()
        self.end_turn_button.show()
        if enabled:
            self.enable_action()
        else:
            self.disable_action()

    def enable_action(self):
        self.action_button.enable()
        self.discard_button.enable()

    def disable_action(self):
        self.action_button.disable()
        self.discard_button.disable()

    def hide_all(self):
        self.__enable_dice_rolling = False
        self.__enable_buy = False
        self.__enable_sell = False

        # self.action_button.set_text("  -- ")
        # self.action_button.set_color(Colors.DARK_GRAY)
        # self.end_turn_button.set_text(" -- ")
        # self.end_turn_button.set_color(Colors.DARK_GRAY)

        self.action_button.hide()
        self.discard_button.hide()
        self.end_turn_button.hide()
        self.option_button.hide()
