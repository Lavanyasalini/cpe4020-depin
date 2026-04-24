# lock the fuck in
# MamaBeanie
# Bathroom Lock Monitoring DePIN lock in
# Runs on Raspberry Pi + MPU6050 accelerometer
# Detects physical lock rotation

import time
import json
import requests
import os
from pathlib import Path
from datetime import datetime
import math
import board
import busio
import adafruit_mpu6050
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# Config
VALIDATOR_URL = "placeholder"  # set real URL
COINS_PER_EVENT = 10
MIN_EVENT_GAP = 3.0                # seconds
ROTATION_THRESHOLD_MIN = 30        # degrees
ROTATION_THRESHOLD_MAX = 180
TEST_MODE = False                  # set False for real sensor
WALLET_PATH = Path("wallet.pem")
I2C_RETRY_DELAY = 2.0
REQUEST_TIMEOUT = 5.0

# Wallet with persistent RSA key
class PiWallet:
    def __init__(self, path: Path = WALLET_PATH):
        self.path = path
        if self.path.exists():
            with open(self.path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None)
            print("Loaded existing Pi wallet key.")
        else:
            self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            with open(self.path, "wb") as f:
                f.write(pem)
            try:
                os.chmod(self.path, 0o600)
            except Exception:
                pass
            print(f"Created new Pi wallet and saved key to {self.path}")

        self.public_key = self.private_key.public_key()
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        h = hashes.Hash(hashes.SHA256())
        h.update(pub_bytes)
        self.address = h.finalize().hex()[:16]
        self.pub_pem = pub_bytes.decode('utf-8')
        print(f"Pi Wallet Address: {self.address}")

    def sign_message(self, message_dict):
        # sign canonical json (sorted keys)
        message_bytes = json.dumps(message_dict, sort_keys=True).encode('utf-8')
        signature = self.private_key.sign(
            message_bytes,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return signature

# Safe MPU6050 initialization with fallback
def init_mpu():
    global TEST_MODE
    if TEST_MODE:
        print("TEST_MODE enabled — not initializing MPU6050.")
        return None
    if board is None or busio is None or adafruit_mpu6050 is None:
        print("MPU libraries not available; enabling TEST_MODE.")
        TEST_MODE = True
        return None
    for attempt in range(3):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            # wait until I2C is ready (simple wait)
            t0 = time.time()
            while not i2c.try_lock() and (time.time() - t0) < 1.0:
                time.sleep(0.01)
            # release if we acquired to satisfy adafruit api (they create their I2C internally)
            try:
                i2c.unlock()
            except Exception:
                pass
            mpu = adafruit_mpu6050.MPU6050(i2c)
            print("MPU6050 initialized.")
            return mpu
        except Exception as e:
            print(f"MPU init attempt {attempt+1} failed: {e}")
            time.sleep(I2C_RETRY_DELAY)
    print("Unable to init MPU6050; switching to TEST_MODE.")
    TEST_MODE = True
    return None

def accel_to_angle(ax, ay):
    ang = math.degrees(math.atan2(ay, ax)) % 360
    return ang
def angular_diff(a, b):
    return abs((a - b + 180) % 360 - 180)
class TestSensor:
    def __init__(self):
        self.angle = 0.0
    def read_angle(self):
        # simulate a rotation step occasionally
        self.angle = (self.angle + 45) % 360
        return self.angle

# Initialize components
mpu = init_mpu()
test_sensor = TestSensor() if TEST_MODE else None
wallet = PiWallet()


def get_current_angle(prev_angle=None):
    if TEST_MODE:
        return test_sensor.read_angle()
    try:
        ax, ay, az = mpu.acceleration
        return accel_to_angle(ax, ay)
    except Exception as e:
        # On sensor read error, fallback to TEST_MODE (avoid crashing)
        print(f"Sensor read error: {e} — switching to TEST_MODE")
        global TEST_MODE, test_sensor
        TEST_MODE = True
        test_sensor = TestSensor()
        return test_sensor.read_angle()

# warm up samples
SAMPLES_INIT = 8
print("Warming up sensor and averaging initial angle...")
angles = []
for _ in range(SAMPLES_INIT):
    angles.append(get_current_angle())
    time.sleep(0.05)
prev_angle = sum(angles) / len(angles)
print(f"Initial angle set to {prev_angle:.1f}°")

last_event_time = 0.0

print("Bathroom Lock Monitoring Node STARTED - Waiting for lock rotation...")

while True:
    current_angle = get_current_angle(prev_angle)
    diff = angular_diff(current_angle, prev_angle)
    now = time.time()

    if (ROTATION_THRESHOLD_MIN <= diff <= ROTATION_THRESHOLD_MAX and
        (now - last_event_time) > MIN_EVENT_GAP):

        print(f"Lock rotation detected! Change: {diff:.1f}° (prev {prev_angle:.1f} -> now {current_angle:.1f})")

        # Build payload (do not include signature before signing)
        payload = {
            "type": "mint",
            "from": "sensor_node",
            "to": wallet.address,
            "amount": COINS_PER_EVENT,
            "data": {
                "event": "lock_rotation",
                "angle_change_deg": round(diff, 1),
                "prev_angle_deg": round(prev_angle, 1),
                "angle_deg": round(current_angle, 1),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "timestamp": now,
            "pubkey_pem": wallet.pub_pem  # include public key for validator verification
        }

        signature = wallet.sign_message(payload)
        payload["signature"] = signature.hex()

        # Send to validator with basic retry
        try_count = 0
        max_tries = 3
        backoff = 1.0
        sent_ok = False
        while try_count < max_tries and not sent_ok:
            try:
                resp = requests.post(VALIDATOR_URL, json=payload, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    print(f"Mint request accepted; requested {COINS_PER_EVENT} coins.")
                    last_event_time = now
                    sent_ok = True
                else:
                    print(f"Validator rejected: [{resp.status_code}] {resp.text}")
                    try_count += 1
                    time.sleep(backoff)
                    backoff *= 2
            except Exception as e:
                print(f"Network error sending to validator: {e}")
                try_count += 1
                time.sleep(backoff)
                backoff *= 2
        if not sent_ok:
            print("Failed to send mint request after retries.")

    prev_angle = current_angle
    time.sleep(0.1)

