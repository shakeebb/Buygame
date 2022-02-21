"""
Shows the main menu for the game, gets the user name before starting
"""
import sys
from typing import Optional

import pygame
import pygame_widgets
from pygame.event import Event
from pygame_widgets.button import Button
from pygame_widgets.widget import WidgetBase

from common.gameconstants import *
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
        # Display.init()
        # self.surface = Display.surface()
        self.scr_w, self.scr_h = Display.dims()
        self.x, self.y = self.scr_w // 6, self.scr_h // 6
        self.surface = pygame.Surface(
            (self.scr_w//1.5, self.scr_h//1.5)
        )

        self.controls: [InputText] = []
        self.user_choices: Optional[RadioButton] = None
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
        self.widgets: [WidgetBase] = []
        self.create_screen_layout()
        self.messagebox = None

    def on_user_choice(self, o: RadioButton.Option):
        if len(self.controls) > 1:
            self.controls[0].set_text(o.caption)

    def create_screen_layout(self):
        def_usr = ""
        c_x, c_y = self.scr_w//10, INIT_TILE_SIZE * 1.5
        # if we have exactly one user, its safe to assume it.
        _users = self.game_settings['user_defaults'].keys()
        num_usrs = len(_users)
        if num_usrs == 1:
            def_usr = _users.__iter__().__next__()
        elif num_usrs > 1:
            self.user_choices = RadioButton(21 * TILE_ADJ_MULTIPLIER,
                                            1 * TILE_ADJ_MULTIPLIER,
                                            MAX_NAME_LENGTH + 1,
                                            num_usrs * TILE_ADJ_MULTIPLIER,
                                            on_display=False,
                                            on_option_click=self.on_user_choice,
                                            fill_color=Colors.WHITE)
            for u in _users:
                self.user_choices.add_option(u)
                def_usr = u if len(def_usr) == 0 else def_usr
            self.user_choices.show()

        self.controls.append(InputText(c_x, c_y,
                                       "Type a Name: ",
                                       def_usr,
                                       in_focus=True))
        self.controls.append(InputText(c_x, c_y * 5,
                                       "Connect to Server: ",
                                       self.game_settings['target_server_defaults']['ip'],
                                       max_length=16))

        self.controls.append(InputText(c_x, c_y * 10,
                                       "Connect to Server Port: ",
                                       self.game_settings['target_server_defaults']['port']))

        self.widgets.append(
            Button(
                # Mandatory Parameters
                self.surface,  # Surface to place button on
                self.scr_w//4,  # X-coordinate of top left corner
                self.scr_h//2,  # Y-coordinate of top left corner
                100,  # Width
                50,  # Height

                # Optional Parameters
                text='Login',  # Text to display
                fontSize=22,  # Size of font
                margin=10,  # Minimum distance between text/image and edge of button
                inactiveColour=Colors.LT_GRAY.value,  # Colour of button when not being interacted with
                hoverColour=Colors.GREEN.value,  # Colour of button when being hovered over
                pressedColour=Colors.GRAY.value,  # Colour of button when being clicked
                radius=15,  # Radius of border corners (leave empty for not curved)
                onClick=lambda: self.login(),  # Function to call when clicked on
                onClickParams=()
            )
        )

    def login(self):
        self.wc_state = WelcomeState.INPUT_COMPLETE

    def draw(self, input_game):
        # title = Display.title("Welcome to BuyGame !")
        # self.surface.blit(title, (display_width / 2 - title.get_width() / 2, 50))
        # name = Display.name("Type a Name: " + self.name)
        # self.surface.blit(name, (100, 400))
        for _c in self.controls:
            _c.draw(self.surface)
        if self.user_choices is not None:
            self.user_choices.draw(self.surface)

        # if self.wc_state == WelcomeState.INPUT_COMPLETE:
        #     enter = Display.enter_prompt("In Queue...")
        #     self.surface.blit(enter, (display_width / 2 - title.get_width() / 2, 800))
        # else:
        #     enter = Display.enter_prompt("Press enter to join a game...")
        #     self.surface.blit(enter, (display_width / 2 - title.get_width() / 2, 800))
        if self.messagebox is not None:
            self.messagebox.draw(self.surface)

        input_game.surface.blit(self.surface, (self.x, self.y))
        pygame.display.update()

        if self.wc_state == WelcomeState.GAME_CONNECT:
            log("done display")

    def run(self, input_game=None):
        run = True
        clock = pygame.time.Clock()
        from gui.gameui import GameUI
        assert input_game is None or isinstance(input_game, GameUI)
        g: GameUI = input_game
        logger.reset()
        while run:
            clock.tick(FPS)
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
                    g.reinitialize()
                    g.handshake()
                    return
                    # g.main()
                except (OSError, OverflowError) as e:
                    if self.messagebox is None:
                        if isinstance(e, OSError) and e.errno == 61:
                            msg = f"- Server unavailable. Check [{g.ip}:{g.port}] is correct"
                        elif isinstance(e, OSError) and e.errno == 8:
                            msg = f"- Invalid server address. Check [{g.ip}:{g.port}."
                        else:
                            msg = f"- {e}"
                        self.messagebox = MessageBox(self.surface.get_width(), self.surface.get_height(),
                                                     20, 5,
                                                     msg,
                                                     "ok",
                                                     blink=True
                                                     # ,on_ok=lambda: sys.exit(1)
                                                     )
                        self.messagebox.show()
                        self.cur_input_field = 0
                        self.controls[self.cur_input_field].begin_input()
                        if self.user_choices is not None:
                            self.user_choices.show()
                finally:
                    g = input_game

            # %% GameUI delegation end
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse = pygame.mouse.get_pos()
                    if self.messagebox is not None:
                        if self.messagebox.button_events(*mouse):
                            self.messagebox.destroy(self.surface)
                            self.messagebox = None
                            # self.wc_state = WelcomeState.QUIT
                            # run = False
                            # pygame.quit()
                        continue  # modal dialog box.

                    if self.user_choices is not None:
                        self.user_choices.click(*mouse)

                if event.type == pygame.QUIT or \
                        (event.type == KEYUP and event.key == K_ESCAPE):
                    run = False
                    quit()

                if event.type == VIDEORESIZE:
                    # screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    Display.resize(event, g.refresh_resolution) if g is not None else None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_RETURN:
                        if self.messagebox is not None:
                            self.messagebox.destroy(self.surface)
                            self.messagebox = None
                            continue

                        c = self.controls[self.cur_input_field]
                        if len(c.text.strip()) == 0:
                            msg = " " + c.p_text + " cannot be empty"
                            self.messagebox = MessageBox(self.surface.get_width(), self.surface.get_height(),
                                                         20, 5,
                                                         msg,
                                                         "ok", blink=True)
                            self.messagebox.show()
                            continue
                        self.move_next_control(event)
                    else:
                        if self.cur_input_field == 0 and \
                                self.user_choices is not None and \
                                self.user_choices.key_up(event):
                            continue

                        mod = event.mod == pygame.KMOD_NONE
                        if mod and (event.key == pygame.K_DOWN or event.key == pygame.K_TAB) \
                                and 0 <= self.cur_input_field < len(self.controls):
                            self.move_next_control(event)
                            continue
                        elif (
                                     mod and event.key == pygame.K_UP
                                     or
                                     (
                                             event.mod & pygame.KMOD_SHIFT and event.key == pygame.K_TAB
                                     )
                             ) and 0 <= self.cur_input_field < len(self.controls):
                            self.move_next_control(event, True)

                        # gets the key name
                        key_name = pygame.key.name(event.key)
                        # converts to uppercase the key name
                        key_name = key_name.lower()
                        self.controls[self.cur_input_field].type(key_name)

            self.surface.fill(Colors.LTS_GRAY.value)
            # self.surface.fill(self.BG)
            pygame_widgets.update(events)  # Call once every loop to allow widgets to render and listen
            self.draw(input_game)

        self.save_gamesettings()

    def save_gamesettings(self):
        with open(CLIENT_SETTINGS_FILE, 'w') as fp:
            yaml.safe_dump(self.game_settings, fp)

    def move_next_control(self, event: Event, reverse=False):
        self.controls[self.cur_input_field].end_input()

        if self.cur_input_field == len(self.controls) - 1 and event.key == pygame.K_RETURN:
            self.login()
            return

        if not reverse and self.cur_input_field < len(self.controls)-1:
            if self.cur_input_field == 0 and self.user_choices is not None:
                self.user_choices.hide()
            self.cur_input_field += 1
        elif reverse and self.cur_input_field > 0:
            self.cur_input_field -= 1
            if self.cur_input_field == 0 and self.user_choices is not None:
                self.user_choices.show()
        else:
            return
        self.controls[self.cur_input_field].begin_input()


# def main():
#     _reset: bool = False
#     _restore: bool = False
#     user = server = ""
#     port = 0
#     import re
#     for i in range(len(sys.argv)):
#         if re.match("-ur|--user-reset", sys.argv[i].lower().strip()):
#             _reset = True
#         elif re.match("-rs|--restore", sys.argv[i].lower().strip()):
#             _restore = True
#         elif re.match("-u[\b]*|--user=", sys.argv[i].lower().strip()):
#             if sys.argv[i].strip() == "-u":
#                 i += 1 if i < len(sys.argv) - 1 else 0
#                 user = sys.argv[i]
#             else:
#                 user = str(sys.argv[i]).split('=')[1]
#
#         elif re.match("-s[\b]*|--server=", sys.argv[i].lower().strip()):
#             if sys.argv[i].strip() == "-s":
#                 i += 1 if i < len(sys.argv) - 1 else 0
#                 server = sys.argv[i]
#             else:
#                 server = str(sys.argv[i]).split('=')[1]
#         elif re.match("-p[\b]*|--port=", sys.argv[i].lower().strip()):
#             if sys.argv[i].strip() == "-p":
#                 i += 1 if i < len(sys.argv) - 1 else 0
#                 port = int(sys.argv[i])
#             else:
#                 port = int(sys.argv[i]).split('=')[1]
#
#     Display.init()
#     _main = MainMenu(_reset, _restore)
#     _main.controls[0].set_text(user if len(user) > 0 else None)
#     _main.controls[1].set_text(server if len(server) > 0 else None)
#     _main.controls[2].set_text(port if port > 0 else None)
#     _main.run()
#
#
# if __name__ == "__main__":
#     main()
