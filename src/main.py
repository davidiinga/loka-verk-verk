from motors import ServoMotor
from networked_motors import AsyncTCP_ServoMotor
import asyncio
import network

mouth_motor = ServoMotor(14, 50, 20, 60)

def do_connect():
    WIFI_SSID = "TskoliVESM"
    WIFI_LYKILORD = "Fallegurhestur"

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(WIFI_SSID, WIFI_LYKILORD)
        while not wlan.isconnected():
            pass

    print('network config:', wlan.ifconfig())


async def main():
    do_connect()

    server = AsyncTCP_ServoMotor(mouth_motor, "0.0.0.0", 8888)
    await server.start()
    print("Server started.")

    while True:
        await asyncio.sleep(1)

asyncio.run(main())
