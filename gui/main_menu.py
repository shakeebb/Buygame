"""
Shows the main menu for the game, gets the user name before starting
"""
import os
import sys
from pathlib import Path

import pygame
from pygame.locals import *

from common.gameconstants import MAX_NAME_LENGTH, CLIENT_SETTINGS_FILE, CLIENT_SETTINGS_TEMPLATE, Colors, \
    CLIENT_DEFAULT_SETTINGS_FILE
from common.logger import log, logger
from common.utils import write_file
from gui.display import Display
import yaml


class InputText:
    def __init__(self, x: int, y: int, prompt,
                 default: str,
                 in_focus: bool = False):
        self.prompt = prompt
        self.text = default
        self.in_focus = in_focus
        self.x = x
        self.y = y

    def set_text(self, txt):
        if txt is None:
            return
        self.text = txt

    def type(self, char):
        if char == "backspace":
            if len(self.text) > 0:
                self.text = self.text[:-1]
        elif char == "space":
            self.text += " "
        elif len(char) == 1:
            self.text += char

        if len(self.text) >= MAX_NAME_LENGTH:
            self.text = self.text[:MAX_NAME_LENGTH]

    def begin_input(self):
        self.in_focus = True

    def end_input(self):
        self.in_focus = False
        # self.settings[self.field] = self.text

    def draw(self, win: pygame.Surface):
        n = Display.name(self.prompt + self.text)
        if self.in_focus:
            txt_f = Display.name(self.prompt)
            _x, _y = (self.x + txt_f.get_width(), self.y + n.get_height())
            pygame.draw.line(win, Colors.BLACK.value,
                             (_x, _y),
                             (_x + n.get_width() - txt_f.get_width(), _y),
                             3)
        win.blit(n, (self.x, self.y))


class MainMenu:
    BG = (255, 255, 255)

    def __init__(self, user_reset: bool, restore_from_default: bool):
        # self.name = ""
        self.waiting = False
        Display.init()
        self.surface = Display.surface()
        self.controls: [InputText] = []
        self.cur_input_field = 0

        write_file(CLIENT_DEFAULT_SETTINGS_FILE, lambda _f:
                   yaml.safe_dump(CLIENT_SETTINGS_TEMPLATE, _f))
        write_file(CLIENT_SETTINGS_FILE, lambda _f:
                   yaml.safe_dump(CLIENT_SETTINGS_TEMPLATE, _f))

        if restore_from_default:
            try:
                with open(CLIENT_DEFAULT_SETTINGS_FILE, 'r') as d_fp:
                    write_file(CLIENT_SETTINGS_FILE, lambda _f:
                               yaml.safe_dump(yaml.safe_load(d_fp), _f))
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

    def create_screen_layout(self):
        def_usr = ""
        # if we have exactly one user, its safe to assume it.
        num_usrs = self.game_settings['user_defaults'].keys()
        if num_usrs.__len__() == 1:
            def_usr = num_usrs.__iter__().__next__()

        self.controls.append(InputText(200, 400,
                                       "Type a Name: ",
                                       def_usr,
                                       in_focus=True))
        self.controls.append(InputText(200, 600,
                                       "Connect to Server: ",
                                       self.game_settings['server_defaults']['ip']))

    def draw(self):
        self.surface.fill(self.BG)
        display_width, display_height = Display.dims()
        title = Display.title("Welcome to BuyGame !")
        self.surface.blit(title, (display_width / 2 - title.get_width() / 2, 50))
        # name = Display.name("Type a Name: " + self.name)
        # self.surface.blit(name, (100, 400))
        for _c in self.controls:
            _c.draw(self.surface)

        if self.waiting:
            enter = Display.enter_prompt("In Queue...")
            self.surface.blit(enter, (display_width / 2 - title.get_width() / 2, 800))
        else:
            enter = Display.enter_prompt("Press enter to join a game...")
            self.surface.blit(enter, (display_width / 2 - title.get_width() / 2, 800))
        Display.show()
        if self.waiting:
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
            if self.waiting:
                # response = self.n.send({-1:[]})
                # if response:
                #     run = False
                log("creating GameUI")
                g = GameUI(self)
                # for player in response:
                # p = PlayerGUI(player)
                # g.players.append(p)
                g.main()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.quit()
                    quit()
                if event.type == VIDEORESIZE:
                    # screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    Display.resize(event, g.refresh_resolution) if g is not None else None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.controls[self.cur_input_field].end_input()
                        self.cur_input_field += 1
                        if self.cur_input_field >= len(self.controls):
                            self.waiting = True
                            log(f"marking end of field entry(s) {self.controls[0].text} {self.controls[1].text}")
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
    import re
    for i in range(len(sys.argv)):
        if re.match("-ur|--user-reset", sys.argv[i].lower().strip()):
            _reset = True
        if re.match("-rs|--restore", sys.argv[i].lower().strip()):
            _restore = True
        if re.match("-u[\b]*|--user=", sys.argv[i].lower().strip()):
            if sys.argv[i].strip() == "-u":
                i += 1 if i < len(sys.argv) - 1 else 0
                user = sys.argv[i]
            else:
                user = str(sys.argv[i]).split('=')[1]

        if re.match("-s[\b]*|--server=", sys.argv[i].lower().strip()):
            if sys.argv[i].strip() == "-s":
                i += 1 if i < len(sys.argv) - 1 else 0
                server = sys.argv[i]
            else:
                server = str(sys.argv[i]).split('=')[1]

    _main = MainMenu(_reset, _restore)
    _main.controls[0].set_text(user if len(user) > 0 else None)
    _main.controls[1].set_text(server if len(server) > 0 else None)
    _main.run()


if __name__ == "__main__":
    main()
