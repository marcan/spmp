#!/usr/bin/python

import serial, os, struct, time, struct, array
from proxy import *
import initlib

import spmp305x as spmp

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

def rgb2fb555(fname):
	rgbd = open(fname, "rb").read()
	do = ""
	l = len(rgbd) / 3
	for i in xrange(l):
		r,g,b = map(ord, rgbd[i*3:i*3+3])
		r >>= 3
		g >>= 3
		b >>= 3
		val = r<<10 | g<<5 | b
		do += struct.pack("<H", val)
	return do

def testpat():
	ldata = ""
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
	return ldata

iface = spmp.iface
proxy = spmp.proxy
regs = spmp.regs

SCRATCH = 0x24700000

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

regs.LCD_DATA_EXT = 0
proxy.write32(0x10000008,0xFFFFFFFF)
proxy.write32(0x10000110,0xFFFFFFFF)

init = len(sys.argv)>1 and sys.argv[1] == 'init'

proxy.set8(LCD_BASE, 1)
regs.LCD_UPDATE = 1
proxy.set8(LCD_BASE+0x1b9, 0x80)

if init:
	regs.LCD_RESET_REG &= ~LCD_RESET
	regs.LCD_RESET_REG |= LCD_RESET
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
	#regs.GFX_BLIT_FROM_X1 = fx1
	#regs.GFX_BLIT_FROM_X2 = fx2
	#regs.GFX_BLIT_FROM_Y1 = fy1
	#regs.GFX_BLIT_FROM_Y2 = fy2
	#regs.GFX_BLIT_TO_X1 = tx1
	#regs.GFX_BLIT_TO_X2 = tx2
	#regs.GFX_BLIT_TO_Y1 = ty1
	#regs.GFX_BLIT_TO_Y2 = ty2
	buf = struct.pack("<HHHHHHHH", fx1, fy1, fx2, fy2, tx1, ty1, tx2, ty2)
	iface.writemem(0x1000A141, buf)
	regs.LCD_UPDATE = 0x3
	#print fx1,fx2,fy1,fy2,tx1,tx2,ty1,ty2

FBA = 0x24200000
FBB = FBA + (LCD_WIDTH * LCD_HEIGHT * 2)

def setFB(a1, a2, size):
	regs.GFX_FB_START = (a1 >> 1)
	regs.GFX_FB_END = (a2 >> 1)
	regs.GFX_FB_WIDTH = size[0]
	regs.GFX_FB_HEIGHT = size[1]
	regs.LCD_UPDATE = 0x2

proxy.memset16(FBA, 0xF800,  320*240*2)
proxy.memset16(FBB, 0x001F,  320*240*2)

cfb = False

img = rgb2fb565("test.rgb")
setFB(FBA, FBB, (240,320))
setup_blit((0,0), (0,0), (240,320))
regs.GFX_BLIT = 1
time.sleep(0.2)

for i in range(0,len(img),LCD_WIDTH*2):
	iface.writemem(FBA+i, img[i:i+LCD_WIDTH*2])
	regs.GFX_BLIT = 1

regs.GFX_BLIT = 1
time.sleep(1)

bw = 48
bh = 48

bx = 0
by = 0

dbx = 2
dby = 2

while True:
	setup_blit((bx,by), (bx,by), (bw,bh))
	regs.GFX_BLIT = 1
	bx += dbx
	by += dby
	if by+dby >= (FB_HEIGHT - bh):
		dby = -2
	if by+dby <= 0:
		dby = 2
	if bx+dbx >= (FB_WIDTH - bw - 1):
		dbx = -2
	if bx+dbx <= 0:
		dbx = 2
