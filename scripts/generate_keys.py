from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

wallet_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

with open("keys/W001.prv.pem", "wb") as f:
    f.write(wallet_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open("keys/W001.pub.pem", "wb") as f:
    f.write(wallet_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

valid_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

with open("keys/validator.prv.pem", "wb") as f:
    f.write(valid_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open("keys/validator.pub.pem", "wb") as f:
    f.write(valid_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))
