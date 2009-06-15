#!/usr/bin/python

import serial, os, struct, time, struct, array
from proxy import *
import initlib

import spmp305x as spmp

import malloc

def rgb2fb565(fname):
	rgbd = open(fname, "rb").read()
	do = ""
	l = len(rgbd) / 3
	for i in xrange(l):
		r,g,b = map(ord, rgbd[i*3:i*3+3])
		r >>= 3
		g >>= 2
		b >>= 3
		val = r<<11 | g<<5 | b
		do += struct.pack("<H", val)
	return do

iface = spmp.iface
proxy = spmp.proxy
regs = spmp.regs

heap = malloc.Heap(0x24200000, 0x24700000)

SCRATCH = heap.malloc(1024*1024)

LCD_HEIGHT = 320
LCD_WIDTH = 240
LCD_BPP = 16

IO_BASE = 0x10000000

LCD_BASE = IO_BASE + 0xA000

LCD_RESET = 0x80

proxy.set32(0x10001108, 8)
proxy.set32(0x10001100, 8)

initlib.proxy = proxy
initlib.spmp = spmp

sys.path.append(os.path.realpath(os.path.dirname(sys.argv[0]))+"/../lcdinits")
import lcdinit

lcd_type = int(sys.argv[1])

upload = 'upload' in sys.argv[2:]

regs.LCD_DATA_EXT = 0
proxy.write32(0x10000008,0xFFFFFFFF)
proxy.write32(0x10000110,0xFFFFFFFF)


proxy.set8(LCD_BASE, 1)
regs.LCD_UPDATE = 1
proxy.set8(LCD_BASE+0x1b9, 0x80)

regs.LCD_RESET_REG &= ~LCD_RESET
regs.LCD_RESET_REG |= LCD_RESET

print "Initializing for LCD Type %d"%lcd_type
lcdinit.master_lcd_init(lcd_type)
print "LCD Init done"

proxy.clear8(LCD_BASE+0x1b2, 1)
proxy.set8(LCD_BASE+0x1ba, 1)
proxy.set8(LCD_BASE+0x1b2, 1)

proxy.write8(LCD_BASE+0x242, 0x5)
proxy.clear8(LCD_BASE+0x203, 0xfe)
proxy.write8(LCD_BASE+0x204, 0xd)
proxy.write8(LCD_BASE+0x205, 0x1)
proxy.set8(LCD_BASE+0x194, 0x4)

proxy.set8(LCD_BASE+0x203, 0x1)

regs.LCD_SCREEN_HEIGHT = LCD_HEIGHT
regs.LCD_SCREEN_WIDTH = LCD_WIDTH
regs.LCD_SCREEN_T1 = 0
regs.LCD_SCREEN_T2 = 0

regs.LCD_UPDATE = 1

proxy.write8(LCD_BASE+0x100, 0x4)
proxy.write8(LCD_BASE+0x1d1, 0xa)
proxy.clear8(LCD_BASE+0x226, 0x1)
proxy.write8(LCD_BASE+0x1db, 0x00)
proxy.write8(LCD_BASE+0x1dc, 0xfc)
proxy.write8(LCD_BASE+0x1dd, 0x00)
proxy.write8(LCD_BASE+0x1de, 0x00)
proxy.write8(LCD_BASE+0x1df, 0xff)
proxy.write8(LCD_BASE+0x1e0, 0xff)

FB_WIDTH = LCD_WIDTH
FB_HEIGHT = LCD_HEIGHT

def setup_blit(fb, disp, size):
	w, h = size
	fx1,fy1 = fb
	fx2,fy2 = fx1 + w - 1, fy1 + h - 1
	tx1,ty1 = disp
	tx2,ty2 = tx1 + w - 1, ty1 + h - 1
	regs.GFX_DRAW_FROM_X1 = fx1
	regs.GFX_DRAW_FROM_X2 = fx2
	regs.GFX_DRAW_SFROM_Y1 = fy1
	regs.GFX_DRAW_FROM_Y2 = fy2
	regs.GFX_DRAW_TO_X1 = tx1
	regs.GFX_DRAW_TO_X2 = tx2
	regs.GFX_DRAW_TO_Y1 = ty1
	regs.GFX_DRAW_TO_Y2 = ty2
	regs.LCD_UPDATE = 0x3

TBIG = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)

def draw():
	sys.stdout.flush()
	regs.GFX_DRAW_START = 1
	while not (regs.GFX_DRAW_STATUS.val & 2):
		pass

def setFB(a1, a2, size):
	regs.GFX_DRAW_SRC = (a1 >> 1)
	regs.GFX_DRAW_SRC2 = (a2 >> 1)
	regs.GFX_DRAW_WIDTH = size[0]
	regs.GFX_DRAW_HEIGHT = size[1]
	regs.LCD_UPDATE = 0x2

setup_blit((0,0), (0,0), (240,320))

setFB(TBIG, TBIG, (240,320))

if upload:
	print "Uploading..."
	img = rgb2fb565("test.rgb")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TBIG+i, img[i:i+LCD_WIDTH*2])
		draw()
	proxy.dc_flushrange(TBIG, len(img))
	draw()
	print "Upload done."
print "Drawing..."
draw()
print "Draw done"
