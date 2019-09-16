#!/usr/bin/python3

DEBUG = 1

#if DEBUG: print('starting program')
import os
import time
import sys
sys.path.append("/home/pi")               # to find local modules from init.d dir

from lcdmodule import LCD
from tempModule import actTemp
from tempModule import setTemp
from pwmModule import PWM

from simple_pid import PID

import pandas as pd
from pandas.plotting import register_matplotlib_converters
#if DEBUG: print('after pandas')
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
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
rt = actTemp(TEMP_ID_1) # actTemp class for RIMS temp sensor

##
## Buttons and LED
##

# GPIO setup
GPIO.setmode(GPIO.BOARD)

# LED setup
PINKLED = 40
GPIO.setup(PINKLED, GPIO.OUT, initial=GPIO.LOW)
pled = GPIO.PWM(PINKLED, 1)             # freq = 1 Hz

# stop button or Mode button
STOPB = 36
GPIO.setup(STOPB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(STOPB, GPIO.FALLING, bouncetime=400)

# instantiate Actual Temp class150)
tt = setTemp(150)

# Up temp button
UPB = 11
GPIO.setup(UPB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(UPB, GPIO.FALLING, callback=(lambda x: tt.upTemp()), bouncetime=400)

# Down temp button
DOWNB = 13
GPIO.setup(DOWNB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(DOWNB, GPIO.FALLING, callback=(lambda x: tt.downTemp()), bouncetime=400)

##
## PWM for heater
##
# PWM config in /boot/config.txt uses default pins
# GPIO_18 = PWM0
# GPIO_19 = PWM1
heater = PWM(0)
heater.period = 2 * 1e9                   # 2 second period
heater.dutyCyclePercent(0.0)

##
## PID controller
##
# Tune with water
# kp = 4.626476953296487
# ki = 0.136835463342823
#kd = 23.48611404618335
#
# Tune from 1.065 mash
# kp = 360
# ki = 8
# kd = 0
#
# Scaled tune from 1.065 mash
# kp = 205.76
# ki = 14.647
# kd=0

# More Scaled tune from 1.065 mash
kp = 115.65
ki = 4.627
kd=0


pid = PID(kp, ki, kd, setpoint=0, sample_time=4)
pid.output_limits = (0, 255)

##
## Instantiate LCD class
##
lcd16 = LCD()
time.sleep(8)                            # display welcome msg

    

def mashControl():
    tt.setTemp(151)                         # set default temp for mashing

    ## Start heater
    heater.start()

    ##
    ## Dataframe for log temps
    ##
    tempHist = pd.DataFrame(columns=['timestamp', 'temp', 'target'])

    # output log file
    logName = "/home/pi/mashTemp.log"
    with open(logName, 'w') as mtl:
        date1 = time.strftime("%Y-%m-%d")
        s = 'Mash Temperature Log for ' + date1 + "\n"
        mtl.write(s)
        # LED Duty cycle = 50%.  So every 2 seconds, it is on for 1 second, then off for 1 sec (freq=0.5Hz) 
        pled.start(50) 
        # read temp once to get the random temp out of there
        tempF = rt.read_temp_f()
        try:
            #Loop to read temp
            while (GPIO.event_detected(STOPB) == False):
                # Generate timestamp
                ts = time.strftime("%Y-%m-%dT%H:%M:%S ", time.localtime())
                #read temp
                tempF = rt.read_temp_f()
    
                #save to dataframe
                tempHist = tempHist.append({'timestamp' : pd.to_datetime(ts), \
                                            'temp' : tempF, \
                                            'target' : tt.target}, \
                                           ignore_index=True)  # append using dictionary
    
                ## Write Logfile
                pstr = ts + " ActualTemp: " +  str(tempF) + "\n"
                mtl.write(pstr)

                lcdTempAndSet(tempF, tt.target)   # display temp
    
                ## Write console window
                if (DEBUG):
                    pstr = "\n" + ts + " ActualTemp: " +  str(tempF)
                    print(pstr)
    
                # PID call
                errTemp = tempF - tt.target # seems to be how simple_pid want it
                outPID = pid(errTemp)
                heater.dutyCyclePercent(outPID/256)
                if DEBUG:
                    s = "errTemp={:.1f}".format(errTemp) + " outPID={:.1f}".format(outPID)
                    print(s)
                    print(str(pid.components))
                    
                ## sleep til next go round
                time.sleep(3)
    
        # allows Control-C to stop loop without printing a trace
        except KeyboardInterrupt:
            pass
    
        if DEBUG: print("\nStopping mash control")

        heater.stop()
        pled.stop()
    
        ##
        ## Plot the mash temp over time
        ##
        dt = time.strftime("%Y-%m-%dT%H-%M", time.localtime())
        mashTsFmt = mdates.DateFormatter("%H:%M")
        plt.ylabel("Temp F")
        plt.xlabel("Time (Hour:Min)")
        #pidtxt = '{:.3f} {:.3f} {:.3f}'.format(kp,ki,kd)
        plt.title("Mash Temperature " + dt)
        ax = plt.axes()
        ax.xaxis.set_major_locator(ticker.MaxNLocator(7))   # set max xticks to 6
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.xaxis.set_major_formatter(mashTsFmt)
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        plt.plot( 'timestamp', 'temp', data=tempHist, color='blue')
        plt.plot( 'timestamp', 'target', data=tempHist, color='yellow')
        plotfile = "/home/pi/plotTemp" + dt + ".png"
        plt.savefig(plotfile, format='png')
    
        # Mash temp statistics
        s = tempHist.describe().to_string() + "\n"
        mtl.write(s)
    
        ##
        ## Save dataframe to csv
        ##
        dff = "/home/pi/tempHist" + dt + ".csv"
        tempHist.to_csv(dff)
    
        # Tell user that files are saved
        lcd16.clear()
        lcd16.write_string("Files saved")
        time.sleep(2)
        
    lf = logName[0:-4] + dt + ".log"
    cmd = "mv " + logName + " " + lf
    os.system(cmd)
                                         # end of mashControl

##
## CIP - clean in place mode
##       - controls temp, but no logs or plot
##
def cip():
    tt.setTemp(130)                         # set default temp for cip

    heater.start()                              # Start heater
    pled.start(35)                              # duty cycle = 35%

    # read temp once to get the random temp out of there
    tempF = rt.read_temp_f()

    try:
        #Loop to read temp
        while (GPIO.event_detected(STOPB) == False):
            #read temp
            tempF = rt.read_temp_f()
    
            ## display temp
            lcdTemp(tempF, tt.target)

            # PID call
            errTemp = tempF - tt.target # seems to be how simple_pid want it
            outPID = pid(errTemp)
            heater.dutyCyclePercent(outPID/256)

            ## sleep til next go round
            time.sleep(3)
    
        # allows Control-C to stop loop without printing a trace
    except KeyboardInterrupt:
        pass
    
    heater.stop()
    pled.stop()
    lcd16.clear()
    if DEBUG: print("\nStopping cip")

def tempMonitor():
    # LED Duty cycle = 50%.  So every 2 seconds, it is on for 1 second, then off for 1 sec (freq=0.5Hz) 
    pled.start(50) 

    # read temp once to get the random temp out of there
    tempF = rt.read_temp_f()

    try:
        #Loop to read temp
        while (GPIO.event_detected(STOPB) == False):
            #read temp
            tempF = rt.read_temp_f()
    
            ## display temp
            lcdTemp(tempF, tt.target)

            ## sleep til next go round
            time.sleep(3)
    
        # allows Control-C to stop loop without printing a trace
    except KeyboardInterrupt:
        pass
    
    pled.stop()
    lcd16.clear()
    if DEBUG: print("\nStopping temp monitor")

def lcdTemp(tempF, target):
    vv = "Temp: " + str(tempF) + chr(223) + "F \r\n"   #\n moves down 1 line
    lcd16.cursor_pos(0,0)
    lcd16.write_string(vv)

def lcdTempAndSet(tempF, target):
    vv = "Temp: " + str(tempF) + chr(223) + "F \r\n"   #\n moves down 1 line
    vv += "Target: " + str(target) + chr(223) +"F"
    lcd16.cursor_pos(0,0)
    lcd16.write_string(vv)


# shutdown the Pi
def shutdown():
    lcd16.clear()
    time.sleep(0.5)
    lcd16.write_string("Shutdown now")
    GPIO.cleanup()
    cmd = "sudo shutdown -h now"
    os.system(cmd)

###
### Modes
###
### These modes: 
### 1) mashing
### 2) just display current temp and allow target to be set
### 3) cip - temp control, but no logging
### 4) shutdown RPi
###
### use mode button to exit the mode and go back to main menu
###
choice = [ "1-Temp Monitor",
                 "2-Mashing       ",
                 "3-CIP              ",
                 "4-Shutdown    " ]
modes = {
    0 : tempMonitor,
    1 : mashControl,
    2 : cip,
    3 : shutdown
    }

firstLine = "Select mode: "
lcd16.clear()
lcd16.cursor_pos(0,0)
lcd16.write_string(firstLine)
modeChoice = 0
while True:
    lcd16.cursor_pos(0,0)
    lcd16.write_string(firstLine)
    lcd16.cursor_pos(1,0)
    lcd16.write_string(choice[modeChoice])

    if (GPIO.event_detected(UPB)):
        lcd16.clear()
        if (modeChoice == 0):
            modeChoice = 3
        else:
            modeChoice -= 1
    elif (GPIO.event_detected(DOWNB)):
        modeChoice = (modeChoice + 1) % 4
        lcd16.clear()
    elif (GPIO.event_detected(STOPB)):
        lcd16.clear()
        # run the selection
        func = modes.get(modeChoice)
        func()
    time.sleep(0.5)
