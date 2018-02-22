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

while button.any() == False:
    print('start of loop')
    f = req.urlopen(link)
    instString = f.read().decode('utf-8') #converts from binary to a string
    inst = json.loads(instString) #converts from string to dictionary
    print(inst)
    print(gyro.value())
    forward = inst['onOff'] == 1
    rotate = abs(gyro.value() - inst['turnAngle']) > 2
    if forward and not rotate:
        motorLeft.run_forever(speed_sp = 300)
        motorRight.run_forever(speed_sp = 300)
    else:
        motorLeft.run_forever(speed_sp = 0)
        motorRight.run_forever(speed_sp = 0)
    if rotate:
        while abs(gyro.value() - inst['turnAngle']) > 1:
            print('    ',gyro.value(),', ',inst['turnAngle'])
            if gyro.value() > inst['turnAngle']:
                motorLeft.run_forever(speed_sp = -90)
                motorRight.run_forever(speed_sp = 90)
            else:
                motorLeft.run_forever(speed_sp = 90)
                motorRight.run_forever(speed_sp = -90)
        motorLeft.run_forever(speed_sp = 0)
        motorRight.run_forever(speed_sp = 0)
print('Ending execution')
