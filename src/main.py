import asyncio
import network
import time

from machine import unique_id, Pin
from binascii import hexlify

from motors import ServoMotor
from mqtt import AsyncMQTT
from networked_components import (
    MQTT_ServoMotor,
    MQTT_RGB_Led,
    MQTT_Neopixel,
    AsyncTCP_AudioPlayer,
)

from rgbs import RGB_Led

def do_connect(ssid: str, password: str):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("connecting to network...")
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass

    print("network config:", wlan.ifconfig())


class Constants:
    MQTT_CLIENT_ID = hexlify(unique_id()).decode()
    MQTT_BROKER_ADDRESS = "10.201.48.114"
    MQTT_BROKER_PORT = 1883

    WIFI_SSID = "TskoliVESM"
    WIFI_PASSWORD = "Fallegurhestur"


class Pins:
    class I2S:
        SCK = 40
        DIN = 39
        LCK = 38

    class Hand:
        HAND_SERVO_MOTOR = 7

    class Skull1:
        MOUTH_SERVO_MOTOR = 17

        class Eyes:
            RED = 12
            GREEN = 11
            BLUE = 10

    class Skull2:
        MOUTH_SERVO_MOTOR = 16

        # class Eyes:
        #     RED = 45
        #     GREEN = 48
        #     BLUE = 35


# MQTT Client
client_id = hexlify(unique_id()).decode()
mqtt_client = AsyncMQTT(client_id, Constants.MQTT_BROKER_ADDRESS, Constants.MQTT_BROKER_PORT)
do_connect(Constants.WIFI_SSID, Constants.WIFI_PASSWORD)
mqtt_client.connect()

# i2s audio
audio_player = AsyncTCP_AudioPlayer(
    Pin(Pins.I2S.SCK),
    Pin(Pins.I2S.LCK),
    Pin(Pins.I2S.DIN),
    "0.0.0.0",
    1337
)

# Hand
hand_servo = MQTT_ServoMotor(
    ServoMotor(Pins.Hand.HAND_SERVO_MOTOR), mqtt_client, "hand_servo"
)

# Skull 1
skull1_mouth_servo = MQTT_ServoMotor(
    ServoMotor(Pins.Skull1.MOUTH_SERVO_MOTOR), mqtt_client, "skull1/mouth_servo"
)
skull1_left_eye = MQTT_RGB_Led(
    RGB_Led(
        Pins.Skull1.Eyes.RED, Pins.Skull1.Eyes.GREEN, Pins.Skull1.Eyes.BLUE
    ),
    mqtt_client,
    "skull1/eyes",
)

# Skull 2
skull2_mouth_servo = MQTT_ServoMotor(
    ServoMotor(Pins.Skull2.MOUTH_SERVO_MOTOR),
    mqtt_client,
    "skull2/mouth_servo",
)
# skull2_left_eye = MQTT_RGB_Led(
#     RGB_Led(
#         Pins.Skull2.Eyes.RED, Pins.Skull2.Eyes.GREEN, Pins.Skull2.Eyes.BLUE
#     ),
#     mqtt_client,
#     "skull2/eyes",
# )

async def main():
    try:
        await mqtt_client.start()
        await audio_player.start()
        

        while True:
            await asyncio.sleep(1)

    finally:
        skull1_mouth_servo.write(0.0)
        skull2_mouth_servo.write(0.0)

asyncio.run(main())