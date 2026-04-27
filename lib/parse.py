from lib.const import Type, Address
from lib.error import BadMessageException

import json
import struct
import socket
from enum import Enum

def next_sep(raw, separator=b"."):
    try:
        return raw.index(separator)
    except ValueError:
        return len(raw)

class Message:
    def __init__(self):
        self.type = Type.BAD
        self.raw = b""

        self.socket = None
        self.address = None
        self.port = None

    def from_socket(s):
        m = Message()
        m.socket = s

        # receive message
        try:
            if s.type == socket.SOCK_STREAM:
                m.raw = s.recv(1024)
                (m.address, m.port) = s.getpeername()
            else:
                (m.raw, (m.address, m.port)) = s.recvfrom(1024)
        except ValueError:
            raise BadMessageException(s)
        except TimeoutError:
            raise m.error("No message.")

        # parse message type
        m.body = m.raw
        m.type = m.get_field(Type)

        return m

    def from_bytes(raw):
        m = Message()
        m.raw = raw

        # parse message type
        m.body = raw
        m.type = m.get_field(Type)

        return m

    def as_json(self):
        return json.loads(self.body.decode())

    def as_type(self, *types):
        if self.type not in types:
            raise self.error("Type {} not allowed.".format(self.type))

        return self

    def apply(self, fn):
        self.body = fn(self.body)

        return self

    def get_field(self, typ):
        if isinstance(typ, type):
            n = next_sep(self.body)
            (raw, self.body) = self.body[:n], self.body[n+1:]

            try:
                if typ == bytes:
                    return raw
                elif typ == str:
                    return raw.decode()
                elif issubclass(typ, Enum):
                    return typ(struct.unpack(">B", raw)[0])
                elif typ == int:
                    return struct.unpack(">I", raw)[0]
                elif typ == float:
                    return struct.unpack(">d", raw)[0]
            except (ValueError, struct.error):
                raise self.error("Malformed message body.")
        else:
            return tuple(self.get_field(subtype) for subtype in typ)

    def get_fields(self, *types):
        return tuple(self.get_field(typ) for typ in types)

    def error(self, message):
        if self.address:
            return BadMessageException(
                self.socket,
                (self.address, self.port),
                message
            )
        else:
            return BadMessageException(
                self.socket, None, message
            )
