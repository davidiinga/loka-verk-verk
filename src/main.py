from machine import Pin
from motors import ServoMotor
import time 

mouth_motor = ServoMotor(14, 50, 60, 90)


while True:
    for i in range(0, 180, 1):
        mouth_motor.write_angle(i)
        time.sleep_ms(10)
        
    for i in range(180, 0, -1):
        mouth_motor.write_angle(i)
        time.sleep_ms(10)
