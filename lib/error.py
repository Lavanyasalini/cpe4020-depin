from socket import SOCK_DGRAM, SOCK_STREAM, SOCK_RAW

_socket_name = {
    SOCK_DGRAM:  "UDP",
    SOCK_STREAM: "TCP",
    SOCK_RAW:    "RAW"
}

class AppException(Exception):
    "Recoverable error resulting from intended use of the app."

class BadMessageException(AppException):
    "Recoverable error resulting from unexpected or malformed messages."

    def __init__(self, socket, address=(None, None), message=None):
        self.socket = socket
        (self.address, self.port) = address
        self.message = message

    def __str__(self):
        res = _socket_name[self.socket.type]

        if self.address:
            res += "@" + self.address

        if self.port:
            res += ":" + str(self.port)

        res += ": Bad message!"

        if self.message:
            res += " " + str(self.message)

        return res
