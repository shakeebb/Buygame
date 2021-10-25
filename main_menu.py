"""
Shows the main menu for the game, gets the user name before starting
"""
import pygame
from pygame.locals import *

from base import Game
from display import Display
from player import Player


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

    def run(self):
        run = True
        clock = pygame.time.Clock()
        g: Game = None
        while run:
            clock.tick(30)
            self.draw()
            player = self.name
            if self.waiting:
                # response = self.n.send({-1:[]})
                # if response:
                #     run = False
                g = Game()
                # for player in response:
                p = Player(player)
                g.players.append(p)
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

        if len(self.name) >= 20:
            self.name = self.name[:20]


if __name__ == "__main__":
    main = MainMenu()
    main.run()
