#!/usr/bin/python

import os
import glob
import time
import RPi.GPIO as GPIO
from RPLCD import CharLCD

# GPIO setup
GPIO.setmode(GPIO.BOARD)

#LCD setup
#lcd = CharLCD(cols=16, rows=2, pin_rs=37, pin_e=35, pins_data=[40, 38, 36, 32, 33, 31, 29, 23])
#lcd.clear()

# load kernel modules
#thermometer setup
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

#sensor id
TEMP_ID_1 = '28-80000027bc2f'
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + TEMP_ID_1)[0]
device_file = device_folder + '/w1_slave'

#read temp subroutine
def readTempRow():
    p = open(device_file, 'r')
    lines = p.readlines()
    p.close()
    return lines

def read_temp_f():
  lines = readTempRow()
  while lines[0].strip()[-3:] != 'YES':
      time.sleep(0.2)
      lines = readTempRow()
  equalsPosition = lines[1].find('t=')
  if equalsPosition != -1:
      tempRaw = lines[1][equalsPosition+2:]
      tempC = float(tempRaw)/1000.0
      tempF = str(round((tempC / 5.0) * 9.0 + 32.0, 1))
  return tempF

#Loop to read temp
while True:
    ## display temp
#    lcd.write_string(u'Temp: ' + tempF + u'\n')
    tempF = read_temp_f()
    print "Temp: " + tempF + "\n"
    time.sleep(1)
