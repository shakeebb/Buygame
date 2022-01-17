"""
Shows the main menu for the game, gets the user name before starting
"""
import os
import sys
import time
from enum import Enum, auto
from pathlib import Path

import pygame
from pygame.locals import *

from common.gameconstants import MAX_NAME_LENGTH, CLIENT_SETTINGS_FILE, CLIENT_SETTINGS_TEMPLATE, Colors, \
    CLIENT_DEFAULT_SETTINGS_FILE, INIT_TILE_SIZE, TILE_ADJ_MULTIPLIER, WelcomeState
from common.logger import log, logger
from common.utils import write_file
from gui.button import TextButton, MessageBox, InputText, RadioButton
from gui.display import Display
import yaml


class MainMenu:
    BG = (255, 255, 255)

    def __init__(self, user_reset: bool, restore_from_default: bool):
        # self.name = ""
        self.wc_state = WelcomeState.INIT
        Display.init()
        self.surface = Display.surface()
        self.controls: [InputText] = []
        self.user_choices: RadioButton = None
        self.cur_input_field = 0

        write_file(CLIENT_DEFAULT_SETTINGS_FILE, lambda _f:
                   yaml.safe_dump(CLIENT_SETTINGS_TEMPLATE, _f))
        write_file(CLIENT_SETTINGS_FILE, lambda _f:
                   yaml.safe_dump(CLIENT_SETTINGS_TEMPLATE, _f))

        if restore_from_default:
            try:
                with open(CLIENT_DEFAULT_SETTINGS_FILE, 'r') as d_fp:
                    write_file(CLIENT_SETTINGS_FILE, lambda _f:
                               yaml.safe_dump(yaml.safe_load(d_fp), _f),
                               overwrite=True)
            except FileNotFoundError as ffe:
                log("INIT ERROR: ", ffe)

        with open(CLIENT_SETTINGS_FILE) as file:
            try:
                self.game_settings = dict(yaml.safe_load(file))
                if user_reset:
                    self.game_settings['user_defaults'] = {}
            except yaml.YAMLError as exc:
                log("settings.yaml error ", exc)
                pygame.quit()
        self.create_screen_layout()
        self.messagebox = None

    def on_user_choice(self, o: RadioButton.Option):
        self.controls[0].set_text(o.caption)

    def create_screen_layout(self):
        def_usr = ""
        # if we have exactly one user, its safe to assume it.
        _users = self.game_settings['user_defaults'].keys()
        num_usrs = len(_users)
        if num_usrs == 1:
            def_usr = _users.__iter__().__next__()
        elif num_usrs > 1:
            self.user_choices = RadioButton(800//INIT_TILE_SIZE,
                                            300//INIT_TILE_SIZE,
                                            MAX_NAME_LENGTH + 1,
                                            num_usrs * TILE_ADJ_MULTIPLIER,
                                            on_display=False,
                                            on_option_click=self.on_user_choice,
                                            fill_color=Colors.WHITE)
            for u in _users:
                self.user_choices.add_option(u)
            self.user_choices.show()

        self.controls.append(InputText(200, 300,
                                       "Type a Name: ",
                                       def_usr,
                                       in_focus=True))
        self.controls.append(InputText(200, 400,
                                       "Connect to Server: ",
                                       self.game_settings['target_server_defaults']['ip'],
                                       max_length=16))

        self.controls.append(InputText(200, 500,
                                       "Connect to Server Port: ",
                                       self.game_settings['target_server_defaults']['port']))

    def draw(self):
        self.surface.fill(self.BG)
        display_width, display_height = Display.dims()
        title = Display.title("Welcome to BuyGame !")
        self.surface.blit(title, (display_width / 2 - title.get_width() / 2, 50))
        # name = Display.name("Type a Name: " + self.name)
        # self.surface.blit(name, (100, 400))
        for _c in self.controls:
            _c.draw(self.surface)
        if self.user_choices is not None:
            self.user_choices.draw(self.surface)

        if self.wc_state == WelcomeState.INPUT_COMPLETE:
            enter = Display.enter_prompt("In Queue...")
            self.surface.blit(enter, (display_width / 2 - title.get_width() / 2, 800))
        else:
            enter = Display.enter_prompt("Press enter to join a game...")
            self.surface.blit(enter, (display_width / 2 - title.get_width() / 2, 800))
        if self.messagebox is not None:
            self.messagebox.draw(self.surface)
        Display.show()

        if self.wc_state == WelcomeState.GAME_CONNECT:
            log("done display")

    def run(self):
        run = True
        clock = pygame.time.Clock()
        from gui.base import GameUI
        g: GameUI = None
        logger.reset()
        while run:
            clock.tick(30)
            self.draw()
            if self.wc_state == WelcomeState.INPUT_COMPLETE:
                # response = self.n.send({-1:[]})
                # if response:
                #     run = False
                try:
                    if g is None:
                        log("creating GameUI")
                        g = GameUI(self)
                    # for player in response:
                    # p = PlayerGUI(player)
                    # g.players.append(p)
                    g.handshake()
                    g.main()
                except OSError as e:
                    if self.messagebox is None:
                        if e.errno == 61:
                            msg = f"- Server unavailable. Check [{g.ip}:{g.port}] is correct"
                        else:
                            msg = f"- {e}"
                        self.messagebox = MessageBox(self.surface.get_width(), self.surface.get_height(),
                                                     20, 5,
                                                     msg,
                                                     "ok",
                                                     on_ok=lambda : sys.exit(1))
                        self.messagebox.show()
                        self.wc_state = WelcomeState.USER_ERR_CONFIRM
                        # self.wc_state.set_exception(e)
                    time.sleep(1)

            # %% GameUI delegation end

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse = pygame.mouse.get_pos()
                    if self.messagebox is not None:
                        if self.messagebox.button_events(*mouse):
                            self.messagebox = None
                            self.wc_state = WelcomeState.QUIT
                            run = False
                            pygame.quit()
                        continue  # modal dialog box.

                    if self.user_choices is not None:
                        self.user_choices.click(*mouse)

                if event.type == pygame.QUIT or \
                        (event.type == KEYUP and event.key == K_ESCAPE):
                    run = False
                    pygame.quit()
                if event.type == VIDEORESIZE:
                    # screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    Display.resize(event, g.refresh_resolution) if g is not None else None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.controls[self.cur_input_field].end_input()
                        if self.cur_input_field == 0 and self.user_choices is not None:
                            self.user_choices.hide()
                        self.cur_input_field += 1
                        if self.cur_input_field >= len(self.controls):
                            self.wc_state = WelcomeState.INPUT_COMPLETE
                            log(f"marking end of field entry(ies) {self.controls}")
                            continue
                        self.controls[self.cur_input_field].begin_input()
                        # self.n = Network(self.name)
                    else:
                        # gets the key name
                        key_name = pygame.key.name(event.key)
                        # converts to uppercase the key name
                        key_name = key_name.lower()
                        self.controls[self.cur_input_field].type(key_name)

        self.save_gamesettings()

    def save_gamesettings(self):
        with open(CLIENT_SETTINGS_FILE, 'w') as fp:
            yaml.safe_dump(self.game_settings, fp)


def main():
    _reset: bool = False
    _restore: bool = False
    user = server = ""
    port = 0
    import re
    for i in range(len(sys.argv)):
        if re.match("-ur|--user-reset", sys.argv[i].lower().strip()):
            _reset = True
        elif re.match("-rs|--restore", sys.argv[i].lower().strip()):
            _restore = True
        elif re.match("-u[\b]*|--user=", sys.argv[i].lower().strip()):
            if sys.argv[i].strip() == "-u":
                i += 1 if i < len(sys.argv) - 1 else 0
                user = sys.argv[i]
            else:
                user = str(sys.argv[i]).split('=')[1]

        elif re.match("-s[\b]*|--server=", sys.argv[i].lower().strip()):
            if sys.argv[i].strip() == "-s":
                i += 1 if i < len(sys.argv) - 1 else 0
                server = sys.argv[i]
            else:
                server = str(sys.argv[i]).split('=')[1]
        elif re.match("-p[\b]*|--port=", sys.argv[i].lower().strip()):
            if sys.argv[i].strip() == "-p":
                i += 1 if i < len(sys.argv) - 1 else 0
                port = int(sys.argv[i])
            else:
                port = int(sys.argv[i]).split('=')[1]

    _main = MainMenu(_reset, _restore)
    _main.controls[0].set_text(user if len(user) > 0 else None)
    _main.controls[1].set_text(server if len(server) > 0 else None)
    _main.controls[2].set_text(port if port > 0 else None)
    _main.run()


if __name__ == "__main__":
    main()
