from lib.const import Address

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

wallet_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

def make_rsa(name):
    prv = "keys/{}.prv.pem".format(name)
    pub = "keys/{}.pub.pem".format(name)

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    with open(prv, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(pub, "wb") as f:
        f.write(key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

# validator keys
make_rsa("validator")

# wallet keys
for w in Address.WALLETS:
    make_rsa(w)
