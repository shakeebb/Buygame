from enum import Enum, Flag, auto

import pygame as pg
from pygame.constants import *
from pathlib import Path

LOG = True
VERBOSE = False

INIT_TILE_SIZE = 32
DISPLAY_TILE_GRID = False
DISPLAY_TILE_GRID_OUTPUT = False

HEARTBEAT_INTERVAL_SECS = 10.0
WAIT_POLL_INTERVAL = 3.0
STD_HEADER_LENGTH = 10
MAX_RECONNECT_TIME = 16
WILD_CARD = "*"
MAX_LETTERS_ON_HOLD = 8

DEFAULT_SETTINGS_FILE = Path.home().absolute().joinpath('.buygame/.default_settings.yaml')
SETTINGS_FILE = Path.home().absolute().joinpath('.buygame/settings.yaml')
SETTINGS_TEMPLATE = {
    "server_defaults": {
        "ip": "23.239.14.203",
        "port": "1234"
    }
    ,
    "user_defaults": {

    }
}

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
    LTR_GRAY = (180, 180, 180)
    NAVY_BLUE = (60, 60, 100)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 128, 0)
    PURPLE = (255, 0, 255)
    CYAN = (0, 255, 255)
    MAGENTA = (144, 0, 144)
    DIRTY_YELLOW = (240, 170, 0)

    def __init__(self, r, g, b):
        self.R = r
        self.G = g
        self.B = b


class Align(Flag):
    RIGHT = auto()
    LEFT = auto()
    CENTER = auto()


BG_COLOR = Colors.WHITE.value
MAX_NAME_LENGTH = 10
FONT_SIZE = 25
FONT_NAME = "comicsans"
LB_TOP_N = 5
LB_DISP_FMT = " #%s %s [%s] "  # no, name [score]

SURFACE_FLAGS = HWSURFACE | DOUBLEBUF  # | RESIZABLE

EV_DICE_ROLL = pg.USEREVENT + 1
EV_POST_START = EV_DICE_ROLL + 1


class ClientMsgReq(Enum):
    SessionID = "session_id:"
    Name = "name:"
    Start = "start:"
    Dice = "dice:"
    Buy = "buy:"
    Cancel_Buy = "cancel_buy:"
    Sell = "sell:"
    Cancel_Sell = "cancel_sell:"
    Get = "get:"
    HeartBeat = "heartbeat:"
    Is_Done = "is_done:"
    Played = "played:"

    def __init__(self, text: str):
        self.msg: str = text

    @classmethod
    def parse_msg_string(cls, msg_str):
        return cls(msg_str)


class ClientResp(Enum):
    Racks_Ready = "racks ready:"
    Bought = "bought:"
    Buy_Cancelled = "buy_cancelled:"
    Sold = "sold:"
    Sold_Sell_Again = "sold_sell_again:"
    Sell_Cancelled_Sell_Again = "sell_cancelled_sell_again:"
    Sell_Cancelled = "sell_cancelled:"
    Sell_Failed = "sell_failed:"
    Turn_End = "turn ended:"
    Played = "played:"
    Done = "done:"
    Not_Ready = "not_ready:"

    def __init__(self, text: str):
        self.msg = text


class GameUIStatus(Enum):
    INITIAL_STATE = auto()
    ERROR = auto()
    WAIT_START = auto()
    PLAY = auto()
    ROLL_DICE = auto()
    PROMPT_DICE_INPUT = auto()
    DICE_ROLL_COMPLETE = auto()
    WAIT_TURN = auto()
    RECEIVE_RACKS = auto()
    ENABLE_BUY = auto()
    BUY_ENABLED = auto()
    BUY = auto()
    BOUGHT = auto()
    BUY_FAILED = auto()
    CANCEL_BUY = auto()
    BUY_CANCELLED = auto()
    BUY_CANCEL_FAILED = auto()
    ENABLE_SELL = auto()
    SELL_ENABLED = auto()
    SELL = auto()
    CANCEL_SELL = auto()
    SOLD = auto()
    SELL_AGAIN = auto()
    SELL_FAILED = auto()
    I_PLAYED = auto()
    END_TURN = auto()
    TURN_COMPLETE = auto()
    WAIT_ALL_PLAYED = auto()
    ROUND_COMPLETE = auto()