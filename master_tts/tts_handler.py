from audio_streamer import Audio, AudioStreamer
from espeak import Espeak



class TTS_Handler:
    streamer: AudioStreamer
    espeak: Espeak

    def __init__(self, audio_streamer: AudioStreamer, espeak: Espeak):
        self.streamer = audio_streamer
        self.espeak = espeak


    def say_text(self, text: str):
        file_path = "out.wav"
        self.espeak.say_text_to_file(text, file_path)

        audio = Audio.from_wav(file_path)
        self.streamer.start(audio, 512)


if __name__ == "__main__":
    espeak = Espeak()
    streamer = AudioStreamer("10.201.48.52", 1337)
    handler = TTS_Handler(streamer, espeak)

    while True:
        text = input("Enter text: ")
        handler.say_text(text)
