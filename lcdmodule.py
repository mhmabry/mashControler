import RPi.GPIO as GPIO
from RPLCD.gpio import CharLCD

#LCD class
class LCD():
    def __init__(self, name="masher"):
        self.lcd = CharLCD(cols=16, rows=2,
                                    pin_rs=15, pin_e=16,
                                    pins_data=[21, 22, 23, 24],
                                    numbering_mode=GPIO.BOARD,
                                    compat_mode=True)
        self.lcd.clear()
        self.lcd.write_string("Hello " + name)

    def close(self):
        self.lcd.close(clear=True)

    def clear(self):
        self.lcd.clear()

    def write_string(self, string):
        self.lcd.write_string(string)

    def cursor_pos(self, x, y):
        self.lcd.cursor_pos = (x,y)

#LCD setup
# lcd = CharLCD(cols=16, rows=2,
#                       pin_rs=15, pin_rw=18, pin_e=16,
#                       pins_data=[21, 22, 23, 24],
#                       numbering_mode=GPIO.BOARD,
#                       compat_mode=True)
