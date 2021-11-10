from enum import Enum

import pygame as pg
from pygame.constants import *

LOG = True
VERBOSE = False

INIT_TILE_SIZE = 32
DISPLAY_TILE_GRID = False
DISPLAY_TILE_GRID_OUTPUT = False

HEARTBEAT_INTERVAL_SECS = 10.0
MSG_HEADER_LENGTH = 2048
SERIALIZE_HEADER_LENGTH = 4096

FPS = 30  # frames per second, the general speed of the program


# WINDOWWIDTH = 800 # size of window's width in pixels
# WINDOWHEIGHT = 600 # size of windows' height in pixels

class Colors(Enum):
    """
        Colors.XX.value return tuple of (R, G, B)
    """

    BLACK = (0, 0, 0)
    GRAY = (100, 100, 100)
    DARK_GRAY = (128, 128, 128)
    LT_GRAY = (200, 200, 200)
    NAVY_BLUE = (60, 60, 100)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 128, 0)
    PURPLE = (255, 0, 255)
    CYAN = (0, 255, 255)

    def __init__(self, r, g, b):
        self.R = r
        self.G = g
        self.B = b


BG_COLOR = Colors.WHITE.value
MAX_NAME_LENGTH = 10
FONT_SIZE = 25
FONT_NAME = "comicsans"
LB_TOP_N = 5
LB_DISP_FMT = " #%s %s [%s] "  # no, name [score]

SURFACE_FLAGS = HWSURFACE | DOUBLEBUF  # | RESIZABLE

EV_DICE_ROLL = pg.USEREVENT + 1


class ClientMsg(Enum):
    Name = "name: "
    Start = "start"
    Dice = "dice: "
    Bought = "buying racks "
    Sold = "sold: "
    Get = "get"
    HeartBeat = "heartbeat"

    def __init__(self, text: str):
        self.msg = text
