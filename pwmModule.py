import sys
import os

class PWM:
    def __init__(self, chan=0):
        self.channel = chan
        self._period = 1000000000        # in nanoseconds
        self._dutyCycle = 0                     # in nanoseconds
        self._enable = False
        self.path = '/sys/class/pwm/pwmchip0/pwm{:d}'.format(self.channel)

        if not os.path.isdir(self.path):
            raise FileNotFoundError('Directory not found ' + self.path)

    @property
    def period(self):                     # or could read from file in self.path
        return self._period

    @period.setter
    def period(self, ns):
        self._period = int(ns)
        s='{:d}'.format(self._period)
        if DEBUG: print("pwm period=" + s + "\n")
        with open(self.path + '/period', 'w') as f:
            f.write(s)

    @property
    def dutyCycle(self):
        return self._dutyCycle

    @dutyCycle.setter
    def dutyCycle(self, dcns):
        self._dutyCycle = int(dcns)
        if DEBUG: print("pwm dc=" + str(self._dutyCycle) + "\n")
        with open(self.path + '/duty_cycle', 'w') as f:
            f.write('{:d}'.format(self._dutyCycle))

    # Duty Cycle range is 0 - 1.  Percentage of duration
    def dutyCyclePercent(self, dcPercent):
        """Specify duty cycle as a percent (range 0,0 - 1.0)"""
        self.dutyCycle = dcPercent * self.period

    @property
    def enable(self):
        return self._enable

    @enable.setter
    def enable(self, v):
        if v: self._enable = True
        else: self._enable = False

        with open(self.path +'/enable', 'w') as f:
            if v:
                f.write('1')
                if DEBUG: print("Starting pwm")
            else:
                f.write('0')
                if DEBUG: print("Stopping pwm")

    def start(self):
        self.enable = 1

    def stop(self):
        self.enable = 0

