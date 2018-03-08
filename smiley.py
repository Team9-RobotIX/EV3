#! /usr/bin/env python3

from time import sleep
import ev3dev.auto as ev3
from PIL import Image, ImageOps
from ev3dev.ev3 import *
import pyqrcode
import png

screen = ev3.Screen()

qr = pyqrcode.create('http://18.219.63.23/development/lock')
qr.png('qrGenerated.png', scale=3)

while True:
    screen.clear()

    logo = Image.open('qrGenerated.png')
    screen.image.paste(logo, (0,0))


    # Update lcd display
    screen.update()

    #sleep(30)
