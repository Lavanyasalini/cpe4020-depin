from lib.keys import Public, Private
from lib.const import Type, Address
from lib.bytes import concat
from lib.parse import Message
from lib.error import AppException

import json
import socket
import select
from secrets import randbits

# NODE INFO
NODE_ID = "W001"

# KEYS
key = {
    "wallet": Private("keys/W001.prv.pem"),
    "validator": Public("keys/validator.pub.pem")
}

# CONNECTIONS
pending = {}

# FUNCTIONS
def send(data):
    # create dedicated channel
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind((Address.WALLET, 0))
    tcp.listen()

    # generate new session id
    r = randbits(32)

    while r in pending:
        r = randbits(32)

    (local, port) = tcp.getsockname()
    pending[tcp] = {
        "session": r,
        "data": data,
        "ack": 0
    }

    # broadcast REQ (258 bytes)
    try:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        req = concat(
            Type.REQ,
            key["validator"].encrypt(NODE_ID, r, port)
        )

        udp.sendto(req, Address.BROADCAST)
    finally:
        udp.close()

def handle_channel(tcp):
    ch = pending[tcp]
    (tcp_ch, _) = tcp.accept()

    m = Message(tcp_ch)
    
    if m.type == Type.ACK:
        ch["ack"] += 1

        m.apply(key["wallet"].decrypt)
        (validator_id, r) = m.get_fields(str, int)

        # check nonce
        print(ch["ack"], validator_id, r, r == ch["session"])
        # send TKN
        tcp_ch.send(b"SEND DATA HERE.\n" + json.dumps(ch["data"]).encode())

    # close channel
    tcp_ch.close()

def poll():
    try:
        while True:
            (read_ready, _, _) = select.select(pending.keys(), [], [])

            for tcp in read_ready:
                handle_channel(tcp)
    except AppException as e:
        print(e)

def close():
    for s in pending:
        s.close()

if __name__ == "__main__":
    try:
        send({ "test": True })
        send({ "raw": "another packet", "test": False })
        poll()
    finally:
        close()
