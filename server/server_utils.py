import os
import signal


SIGNAL_TRANSLATION_MAP = {
    signal.SIGINT: 'SIGINT',
    signal.SIGTERM: 'SIGTERM',
}


class SignalHandler:
    def __init__(self, sig_user_handler):
        self._pid = os.getpid()
        self._sig = None
        self._frame = None
        self.sig_user_handler = sig_user_handler
        self._old_signal_handler_map = None

    def __enter__(self):
        self._old_signal_handler_map = {
            sig: signal.signal(sig, self._handler)
            for sig, _ in SIGNAL_TRANSLATION_MAP.items()
        }

    def __exit__(self, exc_type, exc_val, exc_tb):
        for sig, handler in self._old_signal_handler_map.items():
            signal.signal(sig, handler)

        if self._sig is None:
            return

        # self._old_signal_handler_map[self._sig](self._sig, self._frame)

    def _handler(self, sig, frame):
        self._sig = sig
        self._frame = frame
        self.sig_user_handler(sig, frame)
