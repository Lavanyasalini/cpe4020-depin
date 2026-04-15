from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

from lib.bytes import concat

class Public:
    def __init__(self, filename):
        with open(filename, "rb") as raw:
            self.key = load_pem_public_key(raw.read())

    def encrypt(self, *parts):
        return self.key.encrypt(
            concat(*parts),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def unsign(self, message):
        signature = message[-256:]
        message = message[:-257]

        self.key.verify(
            signature, message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return message

class Private:
    def __init__(self, filename):
        with open(filename, "rb") as raw:
            self.key = load_pem_private_key(
                raw.read(),
                password=None
            )

    def sign(self, *parts):
        message = concat(*parts)
        
        return concat(
            message,
            self.key.sign(
                message, padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        )

    def decrypt(self, ciphertext):
        return self.key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
