import pickle
import socket
import time
from enum import Enum, auto
from typing import Any

from common.gameconstants import STD_HEADER_LENGTH
from common.logger import log


class ObjectType(Enum):
    OBJECT = auto()
    MESSAGE = auto()
    NOTIFICATION = auto()
    NONE = auto()

    @classmethod
    def parse_msg_string(cls, msg_str):
        return cls(msg_str)


def get_std_hdr(o, m):
    msg_len = len(m)
    # allow 99999999 bytes only as payload size
    assert len(str(msg_len)) <= 8

    return format(o.value, '02d') + format(msg_len, '08d')


def parse_std_hdr(header) -> (ObjectType, int):
    if not len(header):
        return None, 0
    return ObjectType.parse_msg_string(int(header[:2])), int(header[2:])


def serialize(o: ObjectType, v: Any):
    if o == ObjectType.OBJECT:
        a_pickled = pickle.dumps(v)
        std_hdr = get_std_hdr(o, a_pickled)
        return bytes(std_hdr.encode('utf-8') + a_pickled)
    elif o == ObjectType.MESSAGE or o == ObjectType.NOTIFICATION:
        std_hdr = get_std_hdr(o, v)
        return std_hdr.encode('utf-8') + v.encode('utf-8')
    else:
        raise RuntimeError(f"{o} object type not supported")


def deserialize(ot: ObjectType, pl: Any):
    if ot == ObjectType.OBJECT:
        return pickle.loads(pl)
    elif ot == ObjectType.MESSAGE or ot == ObjectType.NOTIFICATION:
        return pl.decode('utf-8')
    else:
        raise RuntimeError(f"{ot} object type not supported")


def receive_pickle(client_socket):
    try:
        message_length = 0
        msg_type: ObjectType = ObjectType.NONE
        while message_length == 0:
            msg_type, message_length = parse_std_hdr(client_socket.recv(STD_HEADER_LENGTH))
            if msg_type is None:
                return False
        assert msg_type == ObjectType.OBJECT

        # print("message_length", message_length)
        message = recvall(client_socket, message_length)
        assert len(message) == message_length

        return deserialize(msg_type, message)
    except Exception as e:
        log("deserialization failed: ", e)
        return False


def receive_message(client_socket, block: bool = False):
    try:
        message_length = 0
        msg_type: ObjectType = ObjectType.NONE
        while message_length == 0:
            msg_type, message_length = parse_std_hdr(client_socket.recv(STD_HEADER_LENGTH))
            if not block and msg_type is None:
                return False
            # time.sleep(0.001)

        assert msg_type == ObjectType.MESSAGE
        return deserialize(msg_type, recvall(client_socket, message_length))
    except Exception as e:
        log("receive message failed with: ", e)
        return False


def recvall(sock, size):
    received_chunks = []
    buf_size = 4096
    remaining = size
    while remaining > 0:
        received = sock.recv(min(remaining, buf_size), socket.MSG_WAITALL)
        # print(f"len(received) {len(received)} remaining {remaining}")
        if not received:
            raise Exception('unexpected EOF')
        received_chunks.append(received)
        remaining -= len(received)
    return b''.join(received_chunks)