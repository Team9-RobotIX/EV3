import threading
import urllib.request as req
import ev3dev.ev3 as ev3
import time
import json
import smbus
import pyqrcode
import png
from PIL import Image, ImageOps

link = 'http://18.219.63.23/flaskapp/'
batchLink = 'http://18.219.63.23/development/instructions/batch'
lockedLink = 'http://18.219.63.23/development/lock'

motorLeft = ev3.LargeMotor('outA')
motorRight = ev3.LargeMotor('outD')
gyro = ev3.GyroSensor(ev3.INPUT_1)
button = ev3.Button()
ultra = ev3.UltrasonicSensor(ev3.INPUT_2)

token = None
locked = None

exitFlag = False
instruction = None


class InstructionThread (threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while not exitFlag:
            self.getInstruction()
            self.getBatchRoute()
            self.getLocked()

    def getInstruction(self):
        global instruction
        global gyro
        global link
        f = req.urlopen(link)
        instString = f.read().decode('utf-8') #converts from binary to a string
        instruction = json.loads(instString) #converts from string to dictionary
        gyro.mode = 'GYRO-RATE' #resets the gyro to 0
        gyro.mode = 'GYRO-ANG'

    def getBatchRoute(self):
        global token
        f = req.urlopen(batchLink)
        batchString = f.read().decode('utf-8') #converts from binary to a string
        batchData = json.loads(batchString) #converts from string to dictionary
        try:
            token = batchData['token']
        except KeyError:
            token = None

    def getLocked(self):
        global locked
        f = req.urlopen(lockedLink)
        lockedString = f.read().decode('utf-8') #converts from binary to a string
        lockedData = json.loads(lockedString) #converts from string to dictionary
        try:
            locked = lockedData['locked']
        except KeyError:
            locked = False

class ExecutionThread (threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def generate_qr(self, token):
        print("token ",token)

        screen = ev3.Screen()
        #print("Creating QR image")
        qr = pyqrcode.create(token)
        qr.png('qrTest.png', scale = 4)

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

        #Lock/unlock
        a = 1 << 5 | 24 | 2 << 1
        b = 0
        if locked:
            b = 255
        bus = smbus.SMBus(6)
        bus.write_i2c_block_data(0x04, a, [b])



        #QR/No QR
        old_token = None
        if token:
            motorLeft.run_forever(speed_sp = 0)
            motorRight.run_forever(speed_sp = 0)
            old_token = token
            self.generate_qr(token)

        screen = ev3.Screen()
        while token:
            if not old_token == token:
                motorLeft.run_forever(speed_sp = 0)
                motorRight.run_forever(speed_sp = 0)
                old_token = token
                self.generate_qr(token)

            motorLeft.run_forever(speed_sp = 0)
            motorRight.run_forever(speed_sp = 0)
            screen.clear()
            qrImage = Image.open('qrTest.png')
            screen.image.paste(qrImage, (0,0))
            screen.update()
        screen.clear()
        screen.update()

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
                motorLeft.run_forever(speed_sp = remaining/1.5 + 20 - c*20)
                motorRight.run_forever(speed_sp = remaining/1.5 + 20 + c*20)
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
            speed = 20
            if abs(diff) < 30:
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

