#! /usr/bin/env python3

from time import sleep
import ev3dev.auto as ev3
from PIL import Image, ImageOps
from ev3dev.ev3 import *
import pyqrcode
import png

#Screen context
screen = ev3.Screen()

qr = pyqrcode.create('http://ec2-18-219-63-23.us-east-2.compute.amazonaws.com/development/lock')
#Creates a corresponding qr code, scaled for the lcd
qr.png('qrGenerated.png', scale=2)


#Show the qr code
while True:
    screen.clear()

    logo = Image.open('qrGenerated.png')
    screen.image.paste(logo, (0,0))

    # Update lcd display
    screen.update()

    sleep(10)
