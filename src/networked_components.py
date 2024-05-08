import struct
import asyncio
import json
from asyncio import StreamReader, StreamWriter

from motors import ServoMotor
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
