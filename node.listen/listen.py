from lib.keys import Public, Private
from lib.const import Type, Address
from lib.bytes import concat
from lib.parse import Message
from lib.error import AppException, BadMessageException

import socket
import select

# NODE INFO
NODE_ID = "V001"

# KEYS
keys = {
    "W001": Public("keys/W001.pub.pem"),
    "validator": Private("keys/validator.prv.pem")
}

# FUNCTIONS
def handle_request(s):
    # parse REQ (258 bytes)
    m = (
        Message(s)
            .parse_type(Type.REQ)
            .apply(keys["validator"].decrypt)
    )

    (node_id, session, port) = m.get_fields(str, int, int)

    # start dedicated channel
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind((Address.VALIDATOR, 0))
    tcp.connect((m.address[0], port))
    tcp.settimeout(0)
    
    # send ACK (258 bytes)
    ack = concat(
        Type.ACK,
        keys[node_id].encrypt(NODE_ID, session, port)
    )

    tcp.send(ack)

    # return dedicated channel
    return tcp

def poll():
    sockets = []

    try:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp.settimeout(0)
        udp.bind(Address.BROADCAST)

        sockets.append(udp)

        while True:
            try:
                (read_ready, _, _) = select.select(sockets, [], [])

                for s in read_ready:
                    if s == udp:
                        tcp = handle_request(udp)
                        sockets.append(tcp)
                    else:
                        raw = s.recv(512)
                        print(raw.decode())

                        # parse TKN
                        # TODO

                        # close channel
                        sockets.remove(s)
                        s.close()

                        # validate data
                        # TODO

                        # send VAL to validator network
                        # TODO

                        # check for consensus
                        # TODO

            except AppException as e:
                print(e)
    finally:
        for s in sockets:
            s.close()

if __name__ == "__main__":
    poll()
