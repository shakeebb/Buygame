import os.path
from enum import Enum, Flag, auto

import pygame as pg
from pygame.constants import *
from pathlib import Path

LOG = True
VERBOSE = False

INIT_TILE_SIZE = 16
TILE_ADJ_MULTIPLIER = 2
DISPLAY_TILE_GRID = False
DISPLAY_TILE_GRID_OUTPUT = False
PLAYER_START_MONEY = 200

BASE_LAYER = 1
INVENTORY_LAYER = 2
SLOT_LAYER = 3
TILE_LAYER = 4
MOVING_TILE_LAYER = 100

HEARTBEAT_INTERVAL_SECS = 10.0
CLEANUP_GAME_IDLE_SECS = 60 * 15
WAIT_POLL_INTERVAL = 3.0
STD_HEADER_LENGTH = 10
MAX_RECONNECT_TIME = 16
WILD_CARD = "*"
MAX_LETTERS_ON_HOLD = 8

# button props
BTN_SH_OFFSET = 5
BTN_CORNER_RAD = 10

CLIENT_DEFAULT_SETTINGS_FILE = Path.home().absolute().joinpath('.buygame/.default_settings.yaml')
CLIENT_SETTINGS_FILE = Path.home().absolute().joinpath('.buygame/client_settings.yaml')
CLIENT_SETTINGS_TEMPLATE = {
    "version": "0.1",
    "target_server_defaults": {
        "ip": "23.239.14.203",
        "port": "36909",
        "socket_timeout": "20"
    }
    ,
    "user_defaults": {

    }
}

SERVER_SETTINGS_FILE = Path.home().absolute().joinpath('.buygame/server_settings.yaml')
STORE_PATH = os.environ.get('STORAGE_PATH')
if STORE_PATH is None:
    STORE_PATH = os.path.dirname(SERVER_SETTINGS_FILE)
STORE_PATH = Path(str(STORE_PATH)).joinpath('data')
SERVER_SETTINGS_TEMPLATE = {
    "version": "0.1",
    "server_defaults": {
        "bind_ip": "0.0.0.0",
        "bind_port": "36909",
        "socket_timeout": "0"
    }
    ,
    "game_settings": {
        "last_gen_id": "0",
        "store_path": f"{STORE_PATH}",
        "player_start_money": f"{PLAYER_START_MONEY}",
        "cleanup_game_idle_secs": f"{CLEANUP_GAME_IDLE_SECS}"
    }
}

FPS = 25  # frames per second, the general speed of the program
MAX_RETRY = 5
NL_DELIM = '\\\\'
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
    LTS_GRAY = (230, 230, 230)
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


BG_COLOR = Colors.WHITE
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
    Skip_Buy = "skip_buy:"
    Sell = "sell:"
    Discard_Sell = "discard_sell:"
    Get = "get:"
    HeartBeat = "heartbeat:"
    EndTurn = "end_turn:"
    Is_Done = "is_done:"
    Played = "played:"

    def __init__(self, text: str):
        self.msg: str = text

    @classmethod
    def parse_msg_string(cls, msg_str):
        return cls(msg_str)


class ClientResp(Enum):
    GET_RET = "get_return:"
    Racks_Ready = "racks ready:"
    Bought = "bought:"
    Buy_Skipped = "buy_skipped:"
    Sold = "sold:"
    Must_Sell = "must_sell:"
    Sell_Cancelled_Sell_Again = "sell_cancelled_sell_again:"
    Sell_Discarded = "sell_discarded:"
    Sell_Failed = "sell_failed:"
    Turn_Ended = "turn_ended:"
    Played = "played:"
    Done = "done:"
    Not_Ready = "not_ready:"
    Cannot_Roll = "cannot_roll:"
    Cannot_Buy = "cannot_buy:"

    def __init__(self, text: str):
        self.msg = text


class GameUIStatus(Enum):
    INITIAL_STATE = auto()
    PLAY = auto()
    ROLL_DICE = auto()
    PROMPT_DICE_INPUT = auto()
    DICE_ROLL_COMPLETE = auto()
    BUY_ENABLED = auto()
    BUY = auto()
    SKIP_BUY = auto()
    SHOW_SELL = auto()
    SELL_DISPLAYED = auto()
    ENABLE_SELL = auto()
    SELL_ENABLED = auto()

    SELL = auto()
    DISCARD_SELL = auto()
    I_PLAYED = auto()
    TERMINATE = auto()

    ERROR = auto()

    END_TURN = auto()
    TURN_COMPLETE = auto()
    WAIT_ALL_PLAYED = auto()
    ROUND_COMPLETE = auto()

    WAIT_START = auto()
    WAIT_TURN = auto()
    RECEIVE_RACKS = auto()
    ENABLE_BUY = auto()
    BOUGHT = auto()
    BUY_FAILED = auto()
    BUY_CANCELLED = auto()
    BUY_CANCEL_FAILED = auto()
    SOLD = auto()
    SELL_AGAIN = auto()
    SELL_FAILED = auto()


class PlayerState(Enum):
    INIT = auto()
    PLAY = auto()
    WAIT = auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"p={self.__repr__()}"


class NotificationType(Enum):
    INFO = auto()
    WARN = auto()
    ERR = auto()
    ACT_1 = auto()
    ACT_2 = auto()
    FLASH = auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"nt={self.__repr__()}"


class Txn(Enum):
    INIT = auto()
    ROLLED = auto()
    BAG_EMPTY = auto()
    NO_BUY = auto()
    BOUGHT = auto()
    BUY_SKIPPED = auto()
    SOLD = auto()
    MUST_SELL = auto()
    SELL_DISCARDED = auto()
    TURN_COMPLETE = auto()
    SELL_CANCELLED_SELL_AGAIN = auto()
    NO_SELL = auto()
    BUY_FAILED = auto()
    BUY_SKIP_FAILED = auto()
    SELL_FAILED = auto()
    SELL_DISCARD_FAILED = auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"tx={self.__repr__()}"


class ConnectionStatus(Enum):
    INIT = auto()
    CONNECTED = auto()
    LEFT = auto()

    def __repr__(self):
        return self.name[:4]

    def __str__(self):
        return f"cs={self.__repr__()}"


class WelcomeState(Enum):
    INIT = auto()
    INPUT_COMPLETE = auto()
    GAME_CONNECT = auto()
    USER_ERR_CONFIRM = auto()
    QUIT = auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"wc={self.__repr__()}"


class InventoryType(Enum):
    BUY_RACK = "Buy Rack"
    WORD_RACK = "Word Rack"
    TILE_RACK = "Tile Rack"
    WILD_CARD_RACK = "WildCard Rack"

    def __init__(self, name):
        self.inv_name = name

    def __repr__(self):
        return self.inv_name

    def __str__(self):
        return self.__repr__()


class GameStage(Enum):
    INIT = auto()
    ROLL = auto()
    BUY = auto()
    SELL = auto()
    ROUND_COMPLETE = auto()
    END_SELL_ONLY = auto()
    TERMINATE = auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"gst={self.__repr__()}"


class GameStatus(Enum):
    START = auto()
    RUNNING = auto()
    PAUSED = auto()
    RESUMED = auto()
    ABANDONED = auto()
    COMPLETED = auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"gs={self.__repr__()}"

