# master_tts

Master text to speech component.
Recieves desired TTS message through MQTT (topic: "tts")
Generates audio files using espeak-ng 
Audio files are then read and sent to the microcontroller through a TCP socket.

The TCP protocol uses ack packets when ready to receive samples.
This helps avoid the microcontroler running out of memory if samples are sent to quickly

## Protocol:
    MQTT Message: 
        topic: tts
        UTF-8 encoded string of the tts message content.
    
    TCP Socket:
        Microcontroller - Server
        Master - Client

        Client connects to the server

        Client sends audio information packet.
            sample rate         : 4 byte unsigned integer
            number of channels  : 4 byte unsigned integer
            bits per sample     : 4 byte unsigned integer
            number of samples   : 4 byte unsigned integer
            samples per packet  : 4 byte unsigned integer

        Server responds with ack packet when ready to recieve audio.
            ack byte literal "0xAD" : 1 byte

        Client sends audio samples 
            samples     : (<bits_per_sample> // 8) * <samples_per_packet> bytes

        Server responds with ack packet when ready to recieve more samples.
            ack byte literal "0xAD" : 1 byte
