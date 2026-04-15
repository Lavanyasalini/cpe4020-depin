from lib.const import Type
from lib.error import BadMessageException

import struct
import json
from enum import Enum

def next_sep(raw, separator=b"."):
    try:
        return raw.index(separator)
    except ValueError:
        return len(raw)

class Message:
    def __init__(self, socket):
        try:
            (self.raw, self.address) = socket.recvfrom(1024)
        except ValueError:
            raise BadMessageException(socket)

        self.socket = socket
        self.body = self.raw
        self.type = self.get_field(Type)

    def parse_type(self, *types):
        if self.type not in types:
            raise self.error("Type {} not allowed.".format(self.type))

        return self

    def apply(self, fn):
        self.body = fn(self.body)

        return self

    def get_field(self, typ):
        n = next_sep(self.body)
        (raw, self.body) = self.body[:n], self.body[n+1:]

        if typ == bytes:
            return raw
        elif typ == str:
            return raw.decode()
        elif issubclass(typ, Enum):
            return typ(struct.unpack(">B", raw)[0])
        elif typ == int:
            return struct.unpack(">I", raw)[0]

    def get_fields(self, *types):
        return tuple(self.get_field(typ) for typ in types)

    def error(self, message):
        return BadMessageException(self.socket, self.address, message)

# PARSE MESSAGE
#class Message:
#    def __init__(self, raw):
#        self.raw = raw
#        self.socket = None
#
#        (type_raw, body_raw) = lsplit(self.raw, 2)
#        self.type = Type(type_raw[0])
#        self.body = body_raw
#
#    def from_socket(socket):
#        (raw, address) = socket.recvfrom(1024)
#
#        try:
#            message = Message(raw)
#        except ValueError:
#            raise BadMessageException(socket, address)
#
#        message.socket = socket
#        message.address = address
#
#        return message
#
#    def as_request(self, body):
#        if self.type != Type.REQUEST:
#            raise self.error("Type {} not allowed.".format(self.type))
#
#        try:
#            self.body = RequestBody(body)
#        except ValueError:
#            return self.error("Malformed request body.")
#
#        return self
#
#    def as_acknowledge(self, body):
#        if self.type != Type.ACKNOWLEDGE:
#            raise self.error("Type {} not allowed.".format(self.type))
#
#        try:
#            self.body = AcknowledgeBody(body)
#        except ValueError:
#            return self.error("Malformed acknowledge body.")
#
#        return self
#
#    def as_query(self, body):
#        if self.type != Type.QUERY:
#            raise self.error("Type {} not allowed.".format(self.type))
#
#        try:
#            self.body = QueryBody(body)
#        except ValueError:
#            return self.error("Malformed query body.")
#
#        return self
#
#    def error(self, message):
#        return BadMessageException(self.socket, self.address, message)
#
#class IDBody:
#    def __init__(self, raw):
#        (id_raw, r_raw) = lsplit(raw, 2)
#
#        self.id = id_raw.decode()
#        self.session_id = struct.unpack(">I", r_raw)[0]
#
#class RequestBody(IDBody):
#    pass
#
#class AcknowledgeBody(IDBody):
#    pass
#
#class QueryBody:
#    def __init__(self, raw):
#        (port_raw, data_raw) = lsplit(raw, 2)
#
#        self.port = struct.unpack(">I", port_raw)[0]
#        self.data = json.loads(data_raw.decode())
#
## PARSE MESSAGES
## def Request(sck):
##     raw, addr = sck.recvfrom(512)
## 
##     try:
##         msg = Message(raw)
##     except ValueError:
##         raise MsgErr(sck, addr)
## 
##     if msg.type != Type.REQUEST:
##         raise MsgErr(sck, addr, "Type " + msg.type + " not allowed.")
## 
##     try:
##         payload = validator.decrypt(msg.body)
##     except ValueError:
##         raise MsgErr(sck, addr, "Failed to decrypt.")
## 
##     try:
##         req = RequestBody(payload)
##     except ValueError:
##         raise MsgErr(sck, addr, "Malformed request body.")
## 
##     return addr, req
## 
