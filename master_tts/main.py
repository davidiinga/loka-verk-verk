import asyncio

from espeak import Espeak
from audio_streamer import AudioStreamer
from tts_handler import TTS_Handler
from mqtt_client import MQTT_Client

mqtt_client = MQTT_Client("RBPI-Master", "10.201.48.114")

espeak = Espeak()
streamer = AudioStreamer("10.201.48.52", 1337)
handler = TTS_Handler(streamer, espeak)

async def main():
    mqtt_client.connect()
    await mqtt_client.start()

    def mqtt_tts_callback(topic, message):
        handler.say_text(message.decode("utf-8"))

    mqtt_client.subscribe("tts", mqtt_tts_callback)

    while True:
        await asyncio.sleep(1)


async def non_mqtt_main():
    while True:
        text = input("Enter text: ")
        handler.say_text(text)


if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(non_mqtt_main())