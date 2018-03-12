#! /usr/bin/env python3

import threading
import urllib.request as req
import ev3dev.ev3 as ev3
import time
import json

link = 'http://18.219.63.23/flaskapp/'

motorLeft = ev3.LargeMotor('outA')
motorRight = ev3.LargeMotor('outD')
gyro = ev3.GyroSensor(ev3.INPUT_1)
button = ev3.Button()
ultra = ev3.UltrasonicSensor(ev3.INPUT_2)

exitFlag = False
instruction = None


class InstructionThread (threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while not exitFlag:
            self.getInstruction()

    def getInstruction(self):
        global instruction
        global gyro
        global link
        f = req.urlopen(link)
        instString = f.read().decode('utf-8') #converts from binary to a string
        instruction = json.loads(instString) #converts from string to dictionary
        gyro.mode = 'GYRO-RATE' #resets the gyro to 0
        gyro.mode = 'GYRO-ANG'

class ExecutionThread (threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global button
        global exitFlag
        while not button.any():
            self.execute()
        exitFlag = True

    def execute(self):
        global instruction
        global gyro
        global ultra
        global motorLeft
        global motorRight
        if instruction == None:
            motorLeft.run_forever(speed_sp = 0)
            motorRight.run_forever(speed_sp = 0)
            return
        stop = instruction['onOff'] == 0
        c = instruction['correction']
        if stop:
            motorLeft.run_forever(speed_sp = 0)
            motorRight.run_forever(speed_sp = 0)
            return
        forward = instruction['turnAngle'] == 0
        remaining = instruction['distance']
        if forward:
            ultra.mode = 'US-DIST-CM'
            dist = ultra.value()
            print("DIST:",dist)
            if dist > 100:
                motorLeft.run_forever(speed_sp = remaining/3 + 20 - c*20)
                motorRight.run_forever(speed_sp = remaining/3 + 20 + c*20)
            #motorLeft.run_forever(speed_sp=50)
            #motorRight.run_forever(speed_sp=50)
            if dist < 100:
                motorLeft.run_forever(speed_sp=0)
                motorRight.run_forever(speed_sp=0)
        else:
            targetAngle = instruction['turnAngle'] * 180 / 3.14159
            currentAngle = gyro.value()
            diff = targetAngle - currentAngle #distance to go in degrees
            #speed = (diff*diff)*(80/(180*180)) * 2 + 10
            speed = 25
            if abs(diff) < 20:
                speed = 10
            if diff > 0:
                motorLeft.run_forever(speed_sp = -speed)
                motorRight.run_forever(speed_sp = speed)
            else:
                motorLeft.run_forever(speed_sp = speed)
                motorRight.run_forever(speed_sp = -speed)

print('Starting Execution')

execThread = ExecutionThread()
instrThread = InstructionThread()

execThread.start()
instrThread.start()

execThread.join()
instrThread.join()

motorLeft.run_forever(speed_sp = 0)
motorRight.run_forever(speed_sp = 0)

print('Ending Execution')
