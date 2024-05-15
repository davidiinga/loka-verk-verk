import subprocess

class Espeak:
    espeak_path: str
    voice: str

    def __init__(self, espeak_path: str = 'espeak-ng', voice: str = "en", pitch: int = 50, amplitude: int = 100):
        self.espeak_path = espeak_path
        self.voice = voice
        self.pitch = pitch
        self.amplitude = amplitude

    def call(self, *args):
        subprocess_args = [self.espeak_path, "-v", self.voice, "--sep=*", "-p", str(self.pitch), "-a", str(self.amplitude), *args]
        print(subprocess_args)

        return subprocess.check_output(subprocess_args).decode("utf-8")

    def say_text(self, text: str):
        self.call(text)
    
    def say_phonemes(self, phonemes: list[str]):
        phonemes_string = "".join(phonemes)
        self.call("-m", "-x", f"[[{phonemes_string}]]")

    def say_text_to_file(self, text: str, file_path: str):
        self.call("-w", file_path, text)

    def say_phonemes_to_file(self, phonemes: list[str], file_path: str):
        phonemes_string = "".join(phonemes)
        self.call("-m", "-x", f"[[{phonemes_string}]]", "-w", file_path)

