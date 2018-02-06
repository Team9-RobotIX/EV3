#! /usr/bin/env python3

from time import sleep
import ev3dev.auto as ev3
from PIL import Image, ImageOps
from ev3dev.ev3 import *

screen = ev3.Screen()


while True:
    screen.clear()

    logo = Image.open('qr2.png')
    screen.image.paste(logo, (0,0))


    # Update lcd display
    screen.update()

    sleep(2)

