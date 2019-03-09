#!/usr/bin/python3

import os
import glob
import time
import pandas as pd
import RPi.GPIO as GPIO
from RPLCD import CharLCD

DEBUG = 1

# GPIO setup
GPIO.setmode(GPIO.BOARD)

#LCD setup
#lcd = CharLCD(cols=16, rows=2, pin_rs=37, pin_e=35, pins_data=[40, 38, 36, 32, 33, 31, 29, 23])
#lcd.clear()

##
## Instructions for thermometer setup
##
## 1. At the command prompt, enter: sudo nano /boot/config.txt, then add this to the bottom of the file:
##    dtoverlay=w1–gpio
## 2. Exit Nano, and reboot the Pi (sudo reboot)
## 3. Log in to the Pi again, and at the command prompt enter sudo modprobe w1–gpio
## 4. Then enter sudo modprobe w1-therm
## 5. Change directories to the /sys/bus/w1/devices directory by entering: cd /sys/bus/w1/devices
## 6. Now enter ls to list the devices:
##

##
## thermometer setup
##
# load kernel modules
os.system('/sbin/modprobe w1-gpio')
os.system('/sbin/modprobe w1-therm')

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

# Dataframe to log temps
ts = time.strftime("%Y-%m-%dT%H:%M:%S ", time.localtime())
tempF = 120.1
tempHist = pd.DataFrame([ts, tempF], columns=['timestamp', 'temp'])

# output file
#logName = "/var/www/mashTemp-" + time.strftime("%Y-%m-%d") + ".log"
logName = "/var/www/mashTemp.log"
with open(logName, 'w') as mtl:
    date1 = time.strftime("%Y-%m-%d")
    s = 'Mash Temperature Log for ' + date1 + "\n"
    mtl.write(s)

    #Loop to read temp
    while True:
        # Generate timestamp
        ts = time.strftime("%Y-%m-%dT%H:%M:%S ", time.localtime())
        #read temp
        tempF = read_temp_f()

        #save to dataframe
        tempHist.append([ts, tempF])
            
        ## Write Logfile
        pstr = ts + " ActualTemp: " +  tempF + "\n"
        mtl.write(pstr)
    
        ## display temp
    #    lcd.write_string(u'Temp: ' + tempF + u'\n')

        ## Write console window
        if (DEBUG):
            pstr = ts + " ActualTemp: " +  tempF
            print(pstr)
    
        ## sleep til next go round
        time.sleep(5)
    
mtl.closed
