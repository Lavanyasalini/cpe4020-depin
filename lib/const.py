import ipaddress
from enum import Enum

class Time:
    TIMEOUT = 15.00
    POLL = 0.10

class Type(Enum):
    REQ = 1
    ACK = 3
    TKN = 2
    VAL = 6
    DON = 7

    BAD = 0

    def __str__(self):
        return "'" + self.name + "'"


class Address:
    LOCAL = "10.100.153.11"

    VALIDATORS = {
        "V01": (LOCAL, 6562),
        "V02": (LOCAL, 6563),
        "V03": (LOCAL, 6564),
    }

    WALLETS = {
        "W01": (LOCAL, 0),
        "W02": (LOCAL, 0),
    }

    NETWORK = ipaddress.ip_network(VALIDATORS["V01"][0])
    BROADCAST = (str(NETWORK.broadcast_address), 6561)
