#!/usr/bin/python

import serial, os, struct
from proxy import *

uartdev = os.environ.get("SPMPDEVICE", "/dev/ttyUSB0")
usbuart = serial.Serial(uartdev, 115200)

iface = UartInterface(usbuart, debug=False)
proxy = SPMPProxy(iface, debug=False)

SCRATCH = 0x24700000

LCD_HEIGHT = 320
LCD_WIDTH = 240
LCD_BPP = 16

IO_BASE = 0x10000000

LCD_BASE = IO_BASE + 0xA000
LCD_DATA = LCD_BASE + 0x196
LCD_DATA_EXT = LCD_BASE + 0xE4
LCD_CTRL = LCD_BASE + 0x195

LCD_nRS = 0x04
LCD_CS = 0x20
LCD_WR = 0x40

LCD_DATA_DIR = LCD_BASE + 0x192
LCD_OUT = 0x20

LCD_RESET_REG = LCD_BASE + 0x1B1
LCD_RESET = 0x80

LCD_GFX_ENABLE = LCD_BASE + 0x0F

LCD_FB_HEIGHT = LCD_BASE + 0x1A0
LCD_FB_WIDTH = LCD_BASE + 0x1A2
LCD_FB_UNK = LCD_BASE + 0x19E

proxy.set32(0x10001108, 8)
proxy.set32(0x10001100, 8)


