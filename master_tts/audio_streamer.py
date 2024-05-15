import wave
import struct
import time

import socket

class Audio:
    frames: list[float]
    rate: int
    channels: int
    bits: int

    def __init__(self, samples: list[float], rate: int, channels: int = 1, bits: int = 16):
        self.frames = samples
        self.rate = rate
        self.channels = channels
        self.bits = bits

    @classmethod
    def from_wav(cls, wav_path: str) -> 'Audio':
        with wave.open(wav_path, 'rb') as wav:
            rate = wav.getframerate()
            length = wav.getnframes()
            channels = wav.getnchannels()
            bits = wav.getsampwidth() * 8

            print(rate)
            print(channels)

            frames_raw = wav.readframes(length)
            frames = struct.unpack(f'{length * channels}h', frames_raw)
            frames = [frame / 32768.0 for frame in frames]

            return cls(frames, rate, channels, bits)
        
    def amplify(self, factor: float):
        self.frames = [frame * factor for frame in self.frames]

class AudioStreamer:
    sock: socket.socket
    address: str
    port: int

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port

    def start(self, audio: Audio, packet_size: int = 512):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((self.address, self.port))

        sock.send(
            struct.pack("IIIII", audio.rate, audio.channels, audio.bits, len(audio.frames), packet_size)
        )

        sock.recv(1)

        i = 0
        length = len(audio.frames)
        while i < length:
            expected_packet_size = min(packet_size, length - i)
            frames = audio.frames[i:i + expected_packet_size]

            packet_values = [int(f * 32768.0) for f in frames]

            packet = struct.pack(f"{expected_packet_size}h", *packet_values)
            sock.send(packet)

            sock.recv(1) # read ack packet
            i += expected_packet_size
            time.sleep(1 / audio.rate * expected_packet_size)

if __name__ == "__main__":
    audio = Audio.from_wav("out.wav")
    streamer = AudioStreamer("10.201.48.52", 1337)
    streamer.start(audio, 1024)
