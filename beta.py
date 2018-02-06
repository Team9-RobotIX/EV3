#! /usr/bin/env python3

import urllib.request as req
import ev3dev.ev3 as ev3
import time
import json

link = 'http://18.219.63.23/flaskapp/'

motorLeft = ev3.LargeMotor('outB')
motorRight = ev3.LargeMotor('outC')
gyro = ev3.GyroSensor(ev3.INPUT_1)
button = ev3.Button()

gyro.mode = 'GYRO-RATE'
gyro.mode = 'GYRO-ANG'

print('Starting execution')

desiredAngle = 0
forward = False
turning = False

angle = 0
leftSpeed = 0
rightSpeed = 0

while button.any() == False:

    #reads in the instruction from the web server
    f = req.urlopen(link)
    instString = f.read().decode('utf-8') #converts from binary to a string
    inst = json.loads(instString) #converts from string to dictionary

    forward = inst['onOff'] == 1
    #only move to turning mode if the angle has changed and not already going that way
    #gets the current angle and converts to (-180,180]
    angle = gyro.value() % 360
    if(angle > 180):
        angle = angle - 360
    turning = desiredAngle != inst['turnAngle'] and abs(angle - inst['turnAngle'] > 1)
    desiredAngle = inst['turnAngle']

    left = angle < desiredAngle
    if abs(angle - desiredAngle) > 180: #used to turn the more efficient direction
        left = not left

    print(desiredAngle, angle)

    if forward and not turning: #Roll forward but do not turn
        leftSpeed = 100
        rightSpeed = 100
        if abs(angle - desiredAngle) > 2:
            if left:
                left = 95
                right = 105
            else:
                left = 105
                right = 95

    elif not forward and not turning: #Don't roll forward and don't turn, just stop
        leftSpeed = 0
        rightSpeed = 0

    else:   #Turning, but not the small corrections when going in a straight line
        if left:
            print('left')
            leftSpeed = -30
            rightSpeed = 30
        else:
            print('right')
            leftSpeed = 30
            rightSpeed = -30

    motorRight.run_forever(rightSpeed)
    motorLeft.run_forever(leftSpeed)
print('Ending execution')
