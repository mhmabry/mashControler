import time
import glob

##
## Set Temp Class
##
class setTemp:
    def __init__(self, target=75):
        self.target = target  # degrees F

    def upTemp(self):
        self.target += 1.0

    def downTemp(self):
        self.target -= 1.0

    def setTemp(self, tt):
        self.target = tt 

##
## Actual Temp Class
##
class actTemp:

    def __init__(self, tempId):
        base_dir = '/sys/bus/w1/devices/'
        self.device_folder = glob.glob(base_dir + tempId)[0]
        self.device_file =self.device_folder + '/w1_slave'
        self.tempRaw = ""
        self.tempC = -40
        self.tempF = -40
        
    #read temp subroutine
    def readTempRow(self):
        p = open(self.device_file, 'r')
        lines = p.readlines()
        p.close()
        return lines

    def read_temp_f(self):
        lines = self.readTempRow()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.readTempRow()
        equalsPosition = lines[1].find('t=')
        if equalsPosition != -1:
            self.tempRaw = lines[1][equalsPosition+2:]
            self.tempC = float(self.tempRaw)/1000.0
            self.tempF = float(round((self.tempC / 5.0) * 9.0 + 32.0, 1))
        return self.tempF
