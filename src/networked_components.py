import struct
import asyncio
import json
from asyncio import StreamReader, StreamWriter
from neopixel import NeoPixel
from machine import I2S, Pin

from motors import ServoMotor
from rgbs import RGB_Led
from mqtt import AsyncMQTT

class AsyncTCP_ServoMotor:
    """
    A servo motor controled by an async TCP connection.
    Used for debugging.

    COMMANDS:
        0 - Read. (Read the current value of the motor.)
        1 - Write. (Write a new value to the motor.)
    """

    motor: ServoMotor
    host: str
    port: int
    server: asyncio.Server
    current_value: float

    def __init__(self, motor: ServoMotor, host: str, port: int):
        """
        Initialize a new AsyncTCP_ServoMotor class instance.

        Params:
            motor: The motor to control.
            host: The host to connect to.
        """
        self.motor = motor
        self.host = host
        self.port = port
        self.server = None # type: ignore
        self.current_value = 0.0

    async def start(self):
        if self.server:
            raise Exception("Server already started.")

        self.server = await asyncio.start_server(
            self.handle_connection, self.host, self.port
        )

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter):

        print("Connection established.")

        while True:
            cmd_bytes = await reader.read(1)
            if cmd_bytes is None:
                break
            
            cmd = struct.unpack("B", cmd_bytes)[0]


            if cmd == 0:
                print("Read command.")
                await self.on_read_command(reader, writer)

            elif cmd == 1:
                print("Write command.")
                await self.on_write_command(reader, writer)

            else:
                print(f"Unknown command: {cmd}")

    async def on_read_command(self, reader: StreamReader, writer: StreamWriter):
        resp_packet = struct.pack("f", self.current_value)
        writer.write(resp_packet)

    async def on_write_command(self, reader: StreamReader, writer: StreamWriter):
        value = struct.unpack("f", await reader.read(4))[0]
        self.motor.write_fraction(value)
        self.current_value = value


class MQTT_ServoMotor:
    """
    A servo motor controlled by an MQTT connection.

    The motor will use the following topics:

        <topic_root>/write
            This topic is used to write a new value to the motor.
            Expected payload: a utf-8 encoded json object in the form {"percent": [0.0 - 1.0]}

        <topic_root>/read
            This topic is used to export the current value of the motor.
            Whenever the motor value changes, it will be published to this topic.
            Expected payload: a utf-8 encoded json object in the form {"percent": [0.0 - 1.0]}
    """
    motor: ServoMotor
    mqtt: AsyncMQTT
    topic_root: str
    current_value: float

    def __init__(self, motor: ServoMotor, mqtt: AsyncMQTT, topic_root: str):
        """
        Initialize a new MQTT_ServoMotor class instance.

        Parameters:
            motor (ServoMotor): The motor to control.
            mqtt (AsyncMQTT): The MQTT client to use.
            topic_root (str): The root topic to use for this motor.
        """
        self.motor = motor
        self.mqtt = mqtt
        self.topic_root = topic_root
        self.current_value = 0.0
        self.mqtt.subscribe(self.write_topic, self._on_write_packet, 1)

    def write(self, value: float):
        """
        Write a new value to the motor.
        If the new value differs from the current value a message will be published to the read topic.

        Parameters:
            value (float): The new percentage value for the motor.
        """
        self.motor.write_fraction(value)
        print(value, self.current_value)
        if value != self.current_value:
            self.current_value = value
            self.mqtt.publish(self.read_topic, json.dumps({"percent": value}).encode("utf-8"), 1)

    def read(self) -> float:
        """
        Read the current value of the motor.

        Returns:
            float: The current percentage value of the motor.
        """
        return self.current_value

    async def _on_write_packet(self, topic: str, message: bytes):
        """
        Callback function for the write topic.
        This function will parse the message and write the new value to the motor. 
        """
        message_text = message.decode("utf-8")
        message_data = json.loads(message_text)

        if "percent" in message_data:
            value = message_data["percent"]
            self.write(value)

        else:
            print(f"Invalid MQTT_ServoMotor message: {message_text}")

    @property
    def write_topic(self) -> str:
        return f"{self.topic_root}/write"    
    
    @property
    def read_topic(self) -> str:
        return f"{self.topic_root}/read"


class MQTT_RGB_Led:
    """
    An RGB LED controlled by an MQTT connection.

    The LED will use the following topics:

        <topic_root>/write
            This topic is used to write a new color to the LED.
            Expected payload: a utf-8 encoded json object in the form {"r": [0-255], "g": [0-255], "b": [0-255]}
            Any colors not provided will hold their current value.

        <topic_root>/read
            This topic is used to export the current color of the LED.
            Whenever the LED color changes, it will be published to this topic.
            Expected payload: a utf-8 encoded json object in the form {"r": [0-255], "g": [0-255], "b": [0-255]}
    """

    rgb: RGB_Led
    mqtt: AsyncMQTT
    topic_root: str
    current_color: tuple[int, int, int]

    def __init__(self, rgb: RGB_Led, mqtt: AsyncMQTT, topic_root: str):
        """
        Initialize a new MQTT_RGB_Led class instance.

        Parameters:
            rgb (RGB_Led): The RGB LED to control.
            mqtt (AsyncMQTT): The MQTT client to use.
            topic_root (str): The root topic to use for this LED.
        """
        self.rgb = rgb
        self.mqtt = mqtt
        self.topic_root = topic_root
        self.current_color = (0, 0, 0)

        self.mqtt.subscribe(self.write_topic, self._on_write_packet, 1)


    def write(self, color: tuple[int, int, int]):
        """
        Write a new color to the LED.
        If the new color differs from the current color a message will be published to the read topic.

        Parameters:
            color (tuple[int, int, int]): The new color for the LED.
        """
        self.rgb.set_color(color)
        if color != self.current_color:
            self.current_color = color
            self.mqtt.publish(self.read_topic, json.dumps({"r": color[0], "g": color[1], "b": color[2]}).encode("utf-8"), 1)

    def read(self) -> tuple[int, int, int]:
        """
        Read the current color of the LED.

        Returns:
            tuple[int, int, int]: The current color of the LED.
        """
        return self.current_color
    
    async def _on_write_packet(self, topic: str, message: bytes):
        """
        Callback function for the write topic.
        This function will parse the message and write the new color to the LED. 
        """
        message_text = message.decode("utf-8")
        message_data = json.loads(message_text)

        r = message_data.get("r", self.current_color[0])
        g = message_data.get("g", self.current_color[1])
        b = message_data.get("b", self.current_color[2])

        self.write((r, g, b))

    @property
    def write_topic(self) -> str:
        return f"{self.topic_root}/write"
    
    @property
    def read_topic(self) -> str:
        return f"{self.topic_root}/read"
    

class MQTT_Neopixel:
    """
    A Neopixel controlled by an MQTT connection.

    The Neopixel will use the following topics:

        <topic_root>/write/list
            This topic is used to write a new list of colors to the Neopixel.
            Expected payload: a utf-8 encoded json array of colors in the form [[r, g, b], [r, g, b], ...]
            The length of the array must match the number of leds in the Neopixel.

        <topic_root>/write/single
            This topic is used to write a new color to a single led of the Neopixel.
            Expected payload: a utf-8 encoded json object in the form {"index": [0 - n], "color": [r, g, b]}

        <topic_root>/write/all
            This topic is used to write a new color to all leds of the Neopixel.
            Expected payload: a utf-8 encoded json object in the form {"color": [r, g, b]}

        <topic_root>/read
            This topic is used to export the current colors of the Neopixel.
            Whenever the Neopixel are written, they will be published to this topic.
            Expected payload: a utf-8 encoded json array of colors in the form [[r, g, b], [r, g, b], ...]
    """
    np: NeoPixel
    mqtt: AsyncMQTT
    topic_root: str
    current_colors: list[tuple[int, int, int]] | None
    length: int

    def __init__(self, np: NeoPixel, mqtt: AsyncMQTT, topic_root: str):
        """
        Initialize a new MQTT_Neopixel class instance.

        Parameters:
            np (Neopixel): The Neopixel to control.
            mqtt (AsyncMQTT): The MQTT client to use.
            topic_root (str): The root topic to use for this Neopixel.
        """
        self.np = np
        self.mqtt = mqtt
        self.topic_root = topic_root
        self.current_colors = None
        self.length = np.n

        self.write_all((0, 0, 0))

        self.mqtt.subscribe(self.write_list_topic, self._on_write_list_packet, 1)
        self.mqtt.subscribe(self.write_single_topic, self._on_write_single_packet, 1)
        self.mqtt.subscribe(self.write_all_topic, self._on_write_all_packet, 1)

    def write_list(self, colors: list[tuple[int, int, int]]):
        """
        Write a new list of colors to the Neopixel.

        Parameters:
            colors (list[tuple[int, int, int]]): The new colors for each led of the Neopixel.
        """
        if len(colors) != self.length:
            raise ValueError(f"Attempting to write list of colors with invalid length: {len(colors)} expected: {self.length}")

        for i, color in enumerate(colors):
            self.np[i] = color

        self.np.write()
        self.current_colors = colors
        self.publish_colors()

    def write_single(self, i: int, color: tuple[int, int, int]):
        """
        Write a new color to a single led of the Neopixel.

        Parameters:
            i (int): The index of the led to write to.
            color (tuple[int, int, int]): The new color for the led.
        """
        if i < 0 or i >= self.length:
            raise ValueError(f"Attempting to write color to invalid led index: {i}, expected: 0 - {self.length - 1}")

        self.np[i] = color
        self.np.write()
        self.current_colors[i] = color
        self.publish_colors()

    def write_all(self, color: tuple[int, int, int]):
        """
        Write a new color to all leds of the Neopixel.

        Parameters:
            color (tuple[int, int, int]): The new color for all leds.
        """
        for i in range(self.length):
            self.np[i] = color

        self.np.write()
        self.current_colors = [color] * self.length
        self.publish_colors()

    def read(self) -> list[tuple[int, int, int]]:
        """
        Read the current colors of the Neopixel.

        Returns:
            list[tuple[int, int, int]]: The current colors of the Neopixel.
        """
        return self.current_colors or [(0, 0, 0)] * self.length

    def publish_colors(self):
        """
        Publish the current colors of the Neopixel to the read topic.
        """
        self.mqtt.publish(self.read_topic, json.dumps(self.read()).encode("utf-8"), 1)

    async def _on_write_list_packet(self, topic: str, message: bytes):
        """
        Callback function for the write list topic.
        """
        message_text = message.decode("utf-8")
        message_data = json.loads(message_text)

        colors = [self.validate_color(color) for color in message_data]
        self.write_list(colors)

    async def _on_write_single_packet(self, topic: str, message: bytes):
        """
        Callback function for the write single topic.
        """
        message_text = message.decode("utf-8")
        message_data = json.loads(message_text)

        i = message_data.get("index", None)
        if i is None:
            print(f"Invalid MQTT_Neopixel write single message missing index: {message_text}")
            return

        color = self.validate_color(message_data.get("color", (0, 0, 0)))
        self.write_single(i, color)

    async def _on_write_all_packet(self, topic: str, message: bytes):
        """
        Callback function for the write all topic.
        """
        message_text = message.decode("utf-8")
        message_data = json.loads(message_text)

        color = self.validate_color(message_data.get("color", (0, 0, 0)))
        self.write_all(color)

    @property
    def write_list_topic(self) -> str:
        return f"{self.topic_root}/write/list"
    
    @property
    def write_single_topic(self) -> str:
        return f"{self.topic_root}/write/single"
    
    @property
    def write_all_topic(self) -> str:
        return f"{self.topic_root}/write/all"

    @property
    def read_topic(self) -> str:
        return f"{self.topic_root}/read"

    def validate_color(self, color: tuple[int, int, int]) -> tuple[int, int, int]:
        """
        Clean and validate a color tuple.
        Clamps the values to the range 0 - 255.
        If the color tuple is invalid, returns (0, 0, 0).

        Parameters:
            color (tuple[int, int, int]): The color tuple to validate.

        """
        if len(color) != 3:
            return (0, 0, 0)
        
        return (
            max(0, min(255, color[0])),
            max(0, min(255, color[1])),
            max(0, min(255, color[2]))
        )


class AsyncTCP_AudioPlayer:
    """
    Networked wrapper for the Freenove "Audio Converter & Amplifier" component.

    Communication details:
        Microntroller - Server
        Master - Client

        Clients connects to this server.
        Sends first audio details packet.
            - Sample Rate        : 4 byte unsigned integer
            - Number of channels : 4 byte unsigned integer
            - Bits per sample    : 4 byte unsigned integer
            - Number of samples  : 4 byte unsigned integer
            - Packet Size        : 4 byte unsigned integer

        Server responds with an ack packet
            - 1 byte unsigned integer (0xAD)

        Client sends audio data packets
            - Samples : <Packet Size> * 2 signed integers

        Server responds with an ack packet
            - 1 byte unsigned integer (0xAD)
    """
    sck_pin: Pin
    ws_pin: Pin
    sd_pin: Pin

    host: str
    port: int
    server: asyncio.Server


    def __init__(self, sck_pin: Pin, ws_pin: Pin, sd_pin: Pin, host: str, port: int):
        self.host = host
        self.port = port
        self.sck_pin = sck_pin
        self.ws_pin = ws_pin
        self.sd_pin = sd_pin

    async def start(self):
        self.server = await asyncio.start_server(self.handle_connection, self.host, self.port)

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter):
        print("Connection established.")

        # Read audio details packet
        audio_details = await reader.read(20)
        sample_rate, num_channels, bits_per_sample, num_samples, packet_size = struct.unpack("IIIII", audio_details)

        i2s = I2S(
            1,                  
            sck=self.sck_pin,
            ws=self.ws_pin,
            sd=self.sd_pin,
            mode=I2S.TX,
            bits=bits_per_sample,
            format= I2S.MONO if num_channels == 1 else I2S.STEREO,
            rate=sample_rate,
            ibuf=4000,
        )

        # Send ack packet
        writer.write(struct.pack("B", 0xAD))

        # Audio packet loop
        samples_read = 0
        while samples_read < num_samples:
            audio_packet = await reader.read(packet_size * (bits_per_sample // 8) * num_channels)
            samples_read += packet_size

            # Send ack packet
            writer.write(struct.pack("B", 0xAD))

            i2s.write(audio_packet)


