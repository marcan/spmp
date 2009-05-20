#!/usr/bin/python

import serial, os, struct, time, struct
from proxy import *
import initlib

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

LCD_SCREEN_WIDTH = LCD_BASE + 0x1A0
LCD_SCREEN_HEIGHT = LCD_BASE + 0x1A2
LCD_SCREEN_UNK = LCD_BASE + 0x19E

GFX_BASE = IO_BASE + 0x7000
GFX_BLIT = GFX_BASE + 0x2F
GFX_FB_START = GFX_BASE + 0x130
GFX_FB_END = GFX_BASE + 0x134
GFX_FB_HORIZ = GFX_BASE + 0x138
GFX_FB_VERT = GFX_BASE + 0x13A


proxy.set32(0x10001108, 8)
proxy.set32(0x10001100, 8)

initlib.proxy = proxy
initlib.debug=True

sys.path.append(os.path.realpath(os.path.dirname(sys.argv[0]))+"/../lcdinits")
import lcdinit

proxy.write8(LCD_DATA_EXT,0);
proxy.write32(0x10000008,0xFFFFFFFF)
proxy.write32(0x10000110,0xFFFFFFFF)

init = False

proxy.set8(LCD_BASE, 1)
proxy.write8(LCD_GFX_ENABLE,1)
proxy.set8(LCD_BASE+0x1b9, 0x80)

if init:
	proxy.clear8(LCD_RESET_REG, LCD_RESET)
	proxy.set8(LCD_RESET_REG, LCD_RESET)
	lcdinit.master_lcd_init(6)
else:
	initlib.LCD_WriteReg(0x0f, 0)
	initlib.LCD_WriteReg(0x4f, 0)
	initlib.LCD_SetRegAddr(0x22)

proxy.clear8(LCD_BASE+0x1b2, 1)
proxy.set8(LCD_BASE+0x1ba, 1)
proxy.set8(LCD_BASE+0x1b2, 1)

proxy.write8(LCD_BASE+0x242, 0x5)
proxy.clear8(LCD_BASE+0x203, 0xfe)
proxy.write8(LCD_BASE+0x204, 0xd)
proxy.write8(LCD_BASE+0x205, 0x1)
proxy.set8(LCD_BASE+0x194, 0x4)

proxy.set8(LCD_BASE+0x203, 0x1)

proxy.write16(LCD_SCREEN_HEIGHT, LCD_HEIGHT)
proxy.write16(LCD_SCREEN_WIDTH, LCD_WIDTH)
proxy.write16(LCD_SCREEN_UNK, 0x0505)

proxy.write8(LCD_GFX_ENABLE, 1)

proxy.write8(LCD_BASE+0x100, 0x4)
proxy.write8(LCD_BASE+0x1d1, 0xa)
proxy.clear8(LCD_BASE+0x226, 0x1)
proxy.write8(LCD_BASE+0x1db, 0x00)
proxy.write8(LCD_BASE+0x1dc, 0xfc)
proxy.write8(LCD_BASE+0x1dd, 0x00)
proxy.write8(LCD_BASE+0x1de, 0xff)
proxy.write8(LCD_BASE+0x1df, 0xff)
proxy.write8(LCD_BASE+0x1e0, 0xff)
	
wt = LCD_WIDTH - 1
ht = LCD_HEIGHT - 1
	
proxy.write8(LCD_BASE+0x145, wt & 0xFF)
proxy.write8(LCD_BASE+0x146, wt >> 8)
proxy.write8(LCD_BASE+0x147, ht & 0xFF)
proxy.write8(LCD_BASE+0x148, ht >> 8)
proxy.write8(LCD_BASE+0x14D, wt & 0xFF)
proxy.write8(LCD_BASE+0x14E, wt >> 8)
proxy.write8(LCD_BASE+0x14F, ht & 0xFF)
proxy.write8(LCD_BASE+0x150, ht >> 8)

def setFB(addr):
	proxy.write32(GFX_FB_START,addr>>1)
	proxy.write32(GFX_FB_END,(addr + (320 * 240) ) >>1)
	#proxy.write32(GFX_FB_END,addr>>1)
	proxy.write16(GFX_FB_HORIZ, LCD_WIDTH)
	proxy.write16(GFX_FB_VERT, LCD_HEIGHT)
	proxy.set8(LCD_GFX_ENABLE,2)


ldata = ""

print "a"
for x in range(320):
	for y in range(240):
		bl = (x+y) / 32
		bl += (x-y) / 32
		bl += (x-y) / 32
		clv = ((x - y) & 0x3F) ^ ((x + y) & 0x3F)
		clv2 = clv >> 1
		val = 0
		bl %= 7
		bl += 1
		if bl &1:
			val |= clv2
		if bl &2:
			val |= (clv<<5)
		if bl &4:
			val |= (clv2<<11)
		#else:
		#	val = clv2 | (clv<<5) | (clv2<<11)
		ldata += struct.pack("<H",val)
print "A"

setFB(0x24100000)

initlib.debug=False

proxy.memset16(0x24100000, 0x0000,  320*240*2)
proxy.write8(GFX_BLIT,1)

for i in range(0,len(ldata),LCD_WIDTH*2):
	iface.writemem(0x24100000+i, ldata[i:i+LCD_WIDTH*2])
	#proxy.memset16(0x24100000, 0x003f<<5,  320*240*2)
	proxy.write8(GFX_BLIT,1)
