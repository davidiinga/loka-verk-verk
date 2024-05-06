import struct
import asyncio
from asyncio import StreamReader, StreamWriter

from motors import ServoMotor

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
