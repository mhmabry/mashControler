#!/usr/bin/python3
print('starting program')

import os
import glob
import time
import pandas as pd
print('after pandas')
import RPi.GPIO as GPIO
from RPLCD import CharLCD
import matplotlib.pyplot as plt
print('after imports')

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
## 7. Now enter cd 28-XXXXXXXXXXXX (change the X’s to your own address)
##     For example, in my case I would enter: cd 28-000006637696
## 8. Enter cat w1_slave which will show the raw temperature reading output by the sensor
## 9. Assign the device number (eg. 28-XXXXXXXXXXXX) to TEMP_ID_1 in code below

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
      tempF = float(round((tempC / 5.0) * 9.0 + 32.0, 1))
  return tempF

# Dataframe to log temps
#ts = time.strftime("%Y-%m-%dT%H:%M:%S ", time.localtime())
tempHist = pd.DataFrame(columns=['timestamp', 'temp'])
i = 0

# output file
#logName = "/var/www/mashTemp-" + time.strftime("%Y-%m-%d") + ".log"
#logName = "/var/www/mashTemp.log"
logName = "mashTemp.log"
with open(logName, 'w') as mtl:
    date1 = time.strftime("%Y-%m-%d")
    s = 'Mash Temperature Log for ' + date1 + "\n"
    mtl.write(s)

    try:
        #Loop to read temp
        while True:
            # Generate timestamp
            ts = time.strftime("%Y-%m-%dT%H:%M:%S ", time.localtime())
            #read temp
            tempF = read_temp_f()

            #save to dataframe
            tempHist = tempHist.append({'timestamp' : ts, 'temp' : tempF}, ignore_index=True)  # append using dictionary

            # create graph
            # i = (i +1) %12
            # if (i == 0):
            #     print(tempHist.tail())
            #     plt.plot( 'Timestamp', 'Temp F', data=tempHist)
            #     plt.savefig('plotTemp.png', format='png')
#            matplotlib(tempHist, )

            ## Write Logfile
            pstr = ts + " ActualTemp: " +  str(tempF) + "\n"
            mtl.write(pstr)
    
            ## display temp
        #    lcd.write_string(u'Temp: ' + tempF + u'\n')

            ## Write console window
            if (DEBUG):
                pstr = ts + " ActualTemp: " +  str(tempF)
                print(pstr)
    
            ## sleep til next go round
            time.sleep(5)

    except:
        plt.plot( 'timestamp', 'temp', data=tempHist)
        plt.savefig('plotTemp.png', format='png')
        avg = tempHist['temp'].mean()
        max = tempHist['temp'].max()
        min = tempHist['temp'].min()
        s = "Temp stats:  avg=" + str(avg) + " min=" + str(min) + " max=" + str(max) + "\n"
        mtl.write(s)
        
mtl.closed
