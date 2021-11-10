"""
Shows the main menu for the game, gets the user name before starting
"""
import pygame
from pygame.locals import *

from gui.base import GameUI
from common.gameconstants import MAX_NAME_LENGTH
from common.logger import log, logger
from gui.display import Display


class MainMenu:
    BG = (255, 255, 255)

    def __init__(self):
        self.name = ""
        self.waiting = False
        Display.init()
        self.surface = Display.surface()

    def draw(self):
        self.surface.fill(self.BG)
        display_width, display_height = Display.dims()
        title = Display.title("Welcome to BuyGame !")
        self.surface.blit(title, (display_width / 2 - title.get_width() / 2, 50))
        name = Display.name("Type a Name: " + self.name)
        self.surface.blit(name, (100, 400))
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
                g = GameUI(self.name)
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
                        if len(self.name) > 1:
                            self.waiting = True
                            log("marking end of name entry")
                            # self.n = Network(self.name)
                    else:
                        # gets the key name
                        key_name = pygame.key.name(event.key)
                        # converts to uppercase the key name
                        key_name = key_name.lower()
                        self.type(key_name)

    def type(self, char):
        if char == "backspace":
            if len(self.name) > 0:
                self.name = self.name[:-1]
        elif char == "space":
            self.name += " "
        elif len(char) == 1:
            self.name += char

        if len(self.name) >= MAX_NAME_LENGTH:
            self.name = self.name[:MAX_NAME_LENGTH]


if __name__ == "__main__":
    main = MainMenu()
    main.run()
