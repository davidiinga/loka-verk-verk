# microcontroler_src

The code executed by the microcontroller.
All components are controlled through networking.

Servo motors and LEDs use MQTT topics.
The I2C audio player uses a TCP socket.

Components are callback based so no manual checking is needed.
Main loop starts MQTT server task and audio player task and loops forever.
