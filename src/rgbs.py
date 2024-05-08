from machine import Pin, PWM

class RGB_Led:
    red_pwm: PWM
    green_pwm: PWM
    blue_pwm: PWM

    active_color: tuple[int, int, int]

    def __init__(
        self, red_pin_number: int, green_pin_number: int, blue_pin_number: int
    ):
        self.red_pwm = PWM(Pin(red_pin_number))
        self.green_pwm = PWM(Pin(green_pin_number))
        self.blue_pwm = PWM(Pin(blue_pin_number))

    def set_color(self, colors: tuple[int, int, int]):
        self.red_pwm.duty(colors[0])
        self.green_pwm.duty(colors[1])
        self.blue_pwm.duty(colors[2])
