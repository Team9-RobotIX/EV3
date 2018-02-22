#! /usr/bin/env python3

import threading
import time
import ev3dev.ev3 as ev3
import urllib.request as req

link = 'http://18.219.63.23/api-v2/'

motorLeft  = ev3.LargeMotor('outB')
motorRight = ev3.LargeMotor('outC')
gyro  = ev3.GyroSensor(ev3.INPUT_1)
ultra = ev3.UltrasonicSensor(ev3.INPUT_2)
button = ev3.Button()

exitFlag = False

currentInstruction = None
nextInstruction = None

instructionCompleted = False
completedInstruction = None

updated = False

class Instruction:

    def __init__(self, ID, mode, target):
        self.id = ID
        self.leftSpeed = 0
        self.rightSpeed = 0
        if mode == 0:
            self.mode = 'DRIVE'
        else:
            self.mode = 'TURN'
        self.start = self.detect()
        self.progress = self.start
        self.completed = False
        if self.mode == 'DRIVE':
            self.target = self.start - target
        else:
            self.target = self.start + target
        self.tweak = None

    def detect(self):
        if self.mode == 'DRIVE':
            return ultra.value()
        else:
            return gyro.value()

    def update(self):
        self.progress = self.detect()
        return self.completionCheck()

    def completionCheck(self):
        self.complete = abs(self.target - self.progress) < 2
        if self.complete:
            motorLeft.run_forever(speed_sp = 0)
            motorRight.run_forever(speed_sp = 0)
        return self.complete

    def execute(self):
        if self.mode == 'DRIVE':
            self.executeDrive()
        else:
            self.executeTurn()

    def executeDrive(self):
        self.leftSpeed = 25
        self.rightSpeed = 25
        while not self.update():
            exitFlag = button.any()
            (lTweak, rTweak) = self.getTweak()
            if exitFlag:
                motorLeft.run_forever(speed_sp = 0)
                motorRight.run_forever(speed_sp = 0)
                return
            distance = self.progress - self.target
            boost = distance if distance < 200 else 200
            self.leftSpeed = self.leftSpeed + boost + lTweak
            self.rightSpeed = self.rightSpeed + boost + rTweak
            motorLeft.run_forever(speed_sp = self.leftSpeed)
            motorRight.run_forever(speed_sp = self.rightSpeed)

    def executeTurn(self):
        turnSpeed = 25
        turnDirection = self.progress > self.target
        while not self.update():
            exitFlag = button.any()
            if exitFlag:
                motorLeft.run_forever(speed_sp = 0)
                motorRight.run_forever(speed_sp = 0)
                return
            offset = abs(self.progress - self.target)
            boost = offset / 2
            if turnDirection:
                self.leftSpeed = turnSpeed+boost
                self.rightSpeed = -(turnSpeed+boost)
            else:
                self.leftSpeed = -(turnSpeed+boost)
                self.rightSpeed = turnSpeed+boost
            motorLeft.run_forever(speed_sp = self.leftSpeed)
            motorRight.run_forever(speed_sp = self.rightSpeed)

    def setTweak(self,tweak):
        self.tweak = tweak

    def getTweak():
        if self.tweak == None:
            return (0,0)
        else:
            tweak = self.tweak
            self.tweak = None
            return tweak

class InstructionThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while not exitFlag:
            self.getInstructions()

    def getInstructions(self):
        global currentInstruction
        req.urlopen(link+'instructions')
        instString = f.read().decode('utf-8') #converts from binary to a string
        inst = json.loads(instString) #converts from string to dictionary
        tweak = inst['tweak']
        queue = inst['instructions']
        currentInstruction.setTweak(tweak)


class ExecutionThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global instructionCompleted
        global completedInstruction
        global currentInstruction
        global nextInstruction
        while not exitFlag:
            if not currentInstruction == None:
                currentInstruction.execute()
                instructionCompleted = True
                completedInstruction = currentInstruction
                currentInstruction = nextInstruction
                nextInstruction = None

print('Starting Execution')

execThread = ExecutionThread()
instrThread = InstructionThread()

execThread.start()
instrThread.start()

execThread.join()
instrThread.join()

print('Ending Execution')

motorLeft.run_forever(speed_sp = 0)
motorRight.run_forever(speed_sp = 0)
print('Ending Execution')
