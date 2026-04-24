# lock the fuck in
# MamaBeanie
# Bathroom Lock Monitoring DePIN lock in
# Runs on Raspberry Pi + MPU6050 accelerometer
# Detects physical lock rotation

import time
import json
import requests
from datetime import datetime
import board
import busio
import adafruit_mpu6050
import math
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding



VALIDATOR_URL = "placeholder"   
COINS_PER_EVENT = 10
MIN_EVENT_GAP = 3.0                              # seconds
ROTATION_THRESHOLD_MIN = 30                      # degrees
ROTATION_THRESHOLD_MAX = 180                     # degrees
TEST_MODE = False                                # Set True to test without sensor

# pi wallet
class PiWallet:
    def __init__(self):
        # Generate or load RSA key pair
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # Wallet address 
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.address = hashes.Hash(hashes.SHA256()).update(pub_bytes).finalize().hex()[:16]
        
        print(f"Pi Wallet created! Address: {self.address}")

    def sign_message(self, message_dict):
        """Sign the JSON payload with private key"""
        message_bytes = json.dumps(message_dict, sort_keys=True).encode('utf-8')
        signature = self.private_key.sign(
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

# MPU6050 sensor setup
if not TEST_MODE:
    i2c = busio.I2C(board.SCL, board.SDA)
    mpu = adafruit_mpu6050.MPU6050(i2c)
    print("MPU6050 accelerometer initialized - ready to detect lock rotation")
else:
    print("TEST MODE: No hardware - using fake rotation data")

wallet = PiWallet()
last_event_time = 0
prev_angle = 0.0  # Track previous angle

def get_rotation_angle():
    """Calculate approximate lock rotation angle from acceleration vector"""
    if TEST_MODE:
        # Fake data for testing without hardware
        return (prev_angle + 45) % 360  # simulate turning lock
    
    ax, ay, az = mpu.acceleration
    # for door lock tilt
    magnitude = (ax**2 + ay**2 + az**2)**0.5
    angle = abs(ax) * 90 + abs(ay) * 90  # rough mapping for rotation detection
    return angle % 360

# main loop
print("Bathroom Lock Monitoring Node STARTED - Waiting for lock rotation...")

while True:
    current_angle = get_rotation_angle()
    angle_change = abs(current_angle - prev_angle)
    
    current_time = time.time()
    
    # Check for valid physical lock rotation event
    if (ROTATION_THRESHOLD_MIN <= angle_change <= ROTATION_THRESHOLD_MAX and
        (current_time - last_event_time) > MIN_EVENT_GAP):
        
        print(f" Lock rotation detected! Change: {angle_change:.1f}°")

        # Build mint payload
        payload = {
            "type": "mint",
            "from": "sensor_node",
            "to": wallet.address,
            "amount": COINS_PER_EVENT,
            "data": {
                "event": "lock_rotation",
                "angle_change_deg": round(angle_change, 1),
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": current_time
        }

        # Sign the message
        signature = wallet.sign_message(payload)
        payload["signature"] = signature.hex()   # attach signature

        # Send to validators
        try:
            response = requests.post(VALIDATOR_URL, json=payload, timeout=5)
            if response.status_code == 200:
                print(f" Mint request sent successfully! {COINS_PER_EVENT} coins requested")
                last_event_time = current_time
            else:
                print(f" Validator rejected: {response.text}")
        except Exception as e:
            print(f" Could not reach validators: {e}")

    prev_angle = current_angle
    time.sleep(0.1)  # 100ms loop
