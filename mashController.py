#!/usr/bin/python3

DEBUG = 1

if DEBUG: print('starting program')
import os
import time
import sys
sys.path.append("/home/pi")               # to find local modules from init.d dir
# sys.path.append("/home/pi/.local/lib/python3.5/site-packages")
# Sys.path.append("/home/pi/.local/lib/python3.5/site-packages/numpy")
# sys.path.append("/home/pi/.local/lib/python3.5/site-packages/numpy/core")

from lcdmodule import LCD
from tempModule import actTemp
from tempModule import setTemp
import pandas as pd
from pandas.plotting import register_matplotlib_converters
if DEBUG: print('after pandas')
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
if DEBUG: print('after imports')

register_matplotlib_converters() #explicitly registering a datetime converter for matplotlib with pandas

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
# TEMP_ID_2 = '28-80000027bc2f'   # temp probe from amazon
TEMP_ID_3 = '28-01186e97a1ff'    # Loose temp sensor
TEMP_ID_1 = '28-01186e9576ff'    # temp sensor in RIMS thermowell
rt = actTemp(TEMP_ID_3) # actTemp class for RIMS temp sensor

##
## Buttons and LED
##

# GPIO setup
GPIO.setmode(GPIO.BOARD)

# LED setup
PINKLED = 12
GPIO.setup(PINKLED, GPIO.OUT, initial=GPIO.LOW)
pled = GPIO.PWM(PINKLED, 1)             # freq = 1 Hz

# stop button
STOPB = 36
GPIO.setup(STOPB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(STOPB, GPIO.FALLING)

# instantiate Actual Temp class
tt = setTemp()

# Up temp button
UPB = 11
GPIO.setup(UPB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(UPB, GPIO.FALLING, callback=(lambda x: tt.upTemp()))

# Down temp button
DOWNB = 13
GPIO.setup(DOWNB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(DOWNB, GPIO.FALLING, callback=(lambda x: tt.downTemp()))

##
## PWM for heater
##
# PWM config in /boot/config.txt uses default pins
# GPIO_18 = PWM0
# GPIO_19 = PWM1


##
## Dataframe for log temps
##
tempHist = pd.DataFrame(columns=['timestamp', 'temp'])

#instantiate LCD class
lcd16 = LCD()
time.sleep(10)                            # display welcome msg

# output log file
logName = "/home/pi/mashTemp.log"
with open(logName, 'w') as mtl:
    date1 = time.strftime("%Y-%m-%d")
    s = 'Mash Temperature Log for ' + date1 + "\n"
    mtl.write(s)

    pled.start(50) # Duty cycle = 50%.  So every 2 seconds, it is on for 1 second, then off for 1 sec (freq=0.5Hz)
    i = 0

    try:
        # read temp once to get the random temp out of there
        tempF = rt.read_temp_f()
        if (DEBUG): print("after read_temp_f call")

        #Loop to read temp
        while GPIO.event_detected(STOPB) == False:
            # Generate timestamp
            ts = time.strftime("%Y-%m-%dT%H:%M:%S ", time.localtime())
            #read temp
            tempF = rt.read_temp_f()

            #save to dataframe
            tempHist = tempHist.append({'timestamp' : pd.to_datetime(ts), 'temp' : tempF}, ignore_index=True)  # append using dictionary

            # create graph
            # i = (i +1) %12
            # if (i == 0):
            #     plt.plot( 'timestamp', 'temp', data=tempHist)
            #     plt.savefig('plotTemp.png', format='png')

            ## Write Logfile
            pstr = ts + " ActualTemp: " +  str(tempF) + "\n"
            mtl.write(pstr)
    
            ## display temp
            vv = "Temp: " + str(tempF) + chr(223) + "F \r\n"   #\n moves down 1 line
            vv += "Set:  " + str(tt.target) + chr(223) + "F "  # \r moves to the beginning of the line
            lcd16.cursor_pos(0,0)
            lcd16.write_string(vv)

            ## Write console window
            if (DEBUG):
                pstr = ts + " ActualTemp: " +  str(tempF)
                print(pstr)
    
            ## sleep til next go round
            time.sleep(3)

    except KeyboardInterrupt:
        pass

    if DEBUG: print("\nStopping mash control")
    pled.stop()

    # Plot the mash temp over time
    dt = time.strftime("%Y-%m-%d", time.localtime())
    plt.ylabel("Temp F")
    plt.title("Mash Temperature " + dt)
    plt.plot( 'timestamp', 'temp', data=tempHist)
    plotfile = "/home/pi/plotTemp" + dt + ".png"
    plt.savefig(plotfile, format='png')

    # Mash temp statistics
    # avg = tempHist['temp'].mean()
    # max = tempHist['temp'].max()
    # min = tempHist['temp'].min()
    # s = "Temp stats:  avg=" + str(avg) + " min=" + str(min) + " max=" + str(max) + "\n"
    s = tempHist.describe().to_string() + "\n"
    mtl.write(s)

    # Tell user that files are saved
    lcd16.clear()
    lcd16.write_string("Files saved")

mtl.closed
lf = logName[0:-4] + dt + ".log"
cmd = "mv " + logName + " " + lf
os.system(cmd)
GPIO.cleanup()

