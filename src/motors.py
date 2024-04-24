"""
Module for wrappers around motors.
"""
from machine import Pin, PWM

DUTY_MIN = 0
DUTY_MAX = 1024

class ServoMotor:
    servo_pwm: PWM
    min_value: int
    max_value: int
    
    def __init__(self,
        servo_pin_number: int,
        hz: int = 50,
        min_value: int = 26,
        max_value: int = 130
    ):
        """
        Initialize a new ServoMotor class instance.

        Params:
            servo_pin_number: The number of the pin connected to the servo motor.
            hz: The frequency to use for the motor.
            min_value: The first PWM duty value that generates any movement on the motor.
            max-value: The last PWM duty value that generates any movement on the motor.
        """
        servo_pin = Pin(servo_pin_number)
        self.servo_pwm = PWM(servo_pin, hz)
        self.min_value = min_value
        self.max_value = max_value

    def write_duty(self, duty: int):
        """
        Write a raw PWM duty value to the servo motor.

        Params:
            duty: The duty value to write to the motor.
                  Must be in the range 0 - 1024.
        """
        if duty < DUTY_MIN or duty > DUTY_MAX:
            raise ValueError(f"Attempting to write pwm duty value out of range: {duty}")
        self.servo_pwm.duty(duty)

    def write_angle(self, angle: int):
        """
        Write a given angle to the motor.
        
        params:
            angle: The angle to write to the motor.
                   Must be in the range 0 - 180.
        """
        
        if angle < 0 or angle > 180:
            raise ValueError(f"Attempting to write angle out of range: {angle}")
    
        if angle == 0:
            percent = 0.0
        else:
            percent = angle / 180

        pwm_value = self.min_value + int(percent * (self.max_value - self.min_value))
        self.write_duty(pwm_value)

