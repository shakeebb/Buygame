import pygame
from button import Button, TextButton


class MiddleBar:
    COLORS = {
        0: (255,255,255),
        1: (0,0,0),
        2: (255,0,0),
        3: (0,255,0),
        4: (0,0,255),
        5: (255,255,0),
        6: (255,140,0),
        7: (165,42,42),
        8: (128,0,128)
    }


    def __init__(self, x, y, game):
        self.x = x
        self.y = y
        self.WIDTH = 200
        self.HEIGHT = 100
        self.BORDER_THICKNESS = 5
        self.game = game
        self.gap = 10
        # self.help_button = TextButton(self.x + self.WIDTH - 150, self.y + 25, 100, 50, (128,128,128), "Help")


    def draw(self, win):
        pygame.draw.rect(win, (0,0,0), (self.x, self.y, self.WIDTH, self.HEIGHT), self.BORDER_THICKNESS)
        for i in range(9):
            pygame.draw.rect(win, (0,0,0), ((self.x + i*self.WIDTH/10) + self.gap*(i+1) , self.y + self.gap*0.8, self.WIDTH/10, self.HEIGHT*0.85), self.BORDER_THICKNESS)


        # self.help_button.draw(win)

    def button_events(self):
        """
        handle all button press events here
        :return: None
        """
        mouse = pygame.mouse.get_pos()

        if self.help_button.click(*mouse):
            self.game.chat.update_chat("Help Message")
