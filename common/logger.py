import sys
import threading
import time
from time import strftime, localtime
from datetime import timedelta
import traceback


class Log:
    def __init__(self):
        self.begin = time.perf_counter()

    def reset(self):
        self.begin = time.perf_counter()

    def log_msg(self, msg: str):
        tmp = time.perf_counter()
        print("%s [%s secs] [%s] %s" % (strftime("%Y-%m-%d %H:%M:%S", localtime()),
                                        timedelta(seconds=round((tmp - self.begin))),
                                        threading.currentThread().name, msg))
        self.begin = tmp


logger = Log()


def log(msg):
    if logger is not None:
        if isinstance(msg, Exception):
            ex_info = sys.exc_info()
            logger.log_msg(str(msg))
            traceback.print_exception(*ex_info)
            del ex_info
        else:
            logger.log_msg(msg)
