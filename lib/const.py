from enum import Enum

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
    BROADCAST = ("11.21.7.255", 6561)
    VALIDATOR = "11.21.7.144"
    WALLET    = "11.21.7.144"
