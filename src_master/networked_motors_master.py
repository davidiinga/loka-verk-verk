import socket
import struct
import time

class TCP_ServoMotor_Master:

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def read(self) -> float:
        print("Reading...")
        self.sock.send(struct.pack("B", 0))
        return struct.unpack("f", self.sock.recv(4))[0]
    
    def write(self, value: float) -> None:
        print(f"Writing: {value}")
        self.sock.send(struct.pack("B", 1))
        self.sock.send(struct.pack("f", value))

    def close(self):
        self.sock.close()


if __name__ == "__main__":
    motor = TCP_ServoMotor_Master("10.201.48.52", 8888)

    while True:
        motor.write(0.0)
        time.sleep(1)
        motor.write(1.0)
        time.sleep(1)