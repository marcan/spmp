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

init = 'init' in sys.argv[1:]
upbig = 'upbig' in sys.argv[1:]
uptest = 'uptest' in sys.argv[1:]
upsma = 'upsma' in sys.argv[1:]

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
	#regs.GFX_DRAW_START_FROM_X1 = fx1
	#regs.GFX_DRAW_START_FROM_X2 = fx2
	#regs.GFX_DRAW_START_FROM_Y1 = fy1
	#regs.GFX_DRAW_START_FROM_Y2 = fy2
	#regs.GFX_DRAW_START_TO_X1 = tx1
	#regs.GFX_DRAW_START_TO_X2 = tx2
	#regs.GFX_DRAW_START_TO_Y1 = ty1
	#regs.GFX_DRAW_START_TO_Y2 = ty2
	buf = struct.pack("<HHHHHHHH", fx1, fy1, fx2, fy2, tx1, ty1, tx2, ty2)
	iface.writemem(0x1000A141, buf)
	regs.LCD_UPDATE = 0x3
	#print fx1,fx2,fy1,fy2,tx1,tx2,ty1,ty2

FBA = 0x24200000
FBB = FBA + (LCD_WIDTH * LCD_HEIGHT * 2)

TBIG = FBB
TSMALL = FBB + (LCD_WIDTH * LCD_HEIGHT * 2)


def draw():
	print "Drawing...",
	sys.stdout.flush()
	regs.GFX_DRAW_START = 1
	while not (regs.GFX_DRAW_STATUS.val & 2):
		pass
	print "Done"

def setFB(a1, a2, size):
	regs.GFX_DRAW_SRC = (a1 >> 1)
	regs.GFX_DRAW_SRC2 = (a2 >> 1)
	regs.GFX_DRAW_WIDTH = size[0]
	regs.GFX_DRAW_HEIGHT = size[1]
	regs.LCD_UPDATE = 0x2

proxy.memset16(FBA, 0xF800,  320*240*2)
#proxy.memset16(FBB, 0x001F,  320*240*2)

setup_blit((0,0), (0,0), (240,320))

cfb = False

if upbig:
	setFB(FBB, FBA, (240,320))
	img = rgb2fb565("test.rgb")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TBIG+i, img[i:i+LCD_WIDTH*2])
		draw()
elif uptest:
	setFB(FBB, FBA, (240,320))
	img = rgb2fb565("rgbtest.rgb")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TBIG+i, img[i:i+LCD_WIDTH*2])
		draw()

if upsma:
	img = rgb2fb565("test_small.rgb")
	for i in range(0,len(img),LCD_WIDTH):
		iface.writemem(TSMALL+i, img[i:i+LCD_WIDTH])

setFB(FBA, FBA, (240,320))
draw()

def ballbounce():
	bw = 48
	bh = 48
	
	bx = 0
	by = 0
	
	dbx = 2
	dby = 2
	
	while True:
		setup_blit((bx,by), (bx,by), (bw,bh))
		regs.GFX_DRAW_START = 1
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

def gfx_memcpy(dst, src, size):
	cpmax = 65535
	while size > cpmax:
		gfx_memcpy(dst, src, cpmax)
		dst += cpmax
		src += cpmax
		size -= cpmax
	if size:
		regs.GFX_COPY_OP = 0
		regs.GFX_COPY_OP = 6
		regs.GFX_COPY_SRC = src >> 1
		regs.GFX_COPY_DST = dst >> 1
		regs.GFX_COPY_LSBS = (src & 1) | ((dst & 1) << 1)
		regs.GFX_COPY_BYTE_SIZE = size
		regs.GFX_COPY_START = 1
		while regs.GFX_COPY_FINISHED.val == 0:
			pass
print "Doing"

def cp2(src, a, b, dst, c, d, e=None, f=None):
	# some weird copy... does strange stuff
	if src & 1:
		raise ValueError("Source must be 2-byte aligned")
	if dst & 1:
		raise ValueError("Destination must be 2-byte aligned")
	regs.GFX_COPY_OP = 0
	regs.GFX_COPY_OP = 1

	proxy.write16(IO_BASE + 0x703a, 0xFFFF)
	proxy.write8(IO_BASE + 0x7038, 2)
	
	regs.GFX_COPY_SRC = src>>1
	proxy.write16(IO_BASE + 0x70a4, a)
	proxy.write16(IO_BASE + 0x70a6, b)
	
	regs.GFX_COPY_DEST = dst>>1
	
	e = e or c
	f = f or d
	
	proxy.write16(IO_BASE + 0x70b4, c)
	proxy.write16(IO_BASE + 0x70b6, d)
	proxy.write16(IO_BASE + 0x70bc, e)
	proxy.write16(IO_BASE + 0x70be, f)
	
	regs.GFX_COPY_START = 1
	while regs.GFX_COPY_FINISHED.val == 0:
		pass

#gfx_memcpy(FBA, FBB, LCD_WIDTH * LCD_HEIGHT * 2)

#cp2(TSMALL, 120, 160, FBA+8, 240, 320, 120, 160)

def gfx_blit(src, ssize, spos, dst, dsize, dpos, csize, autoalign=False):
	print "blit %08x %r %r %08x %r %r %r"%(src, ssize, spos, dst, dsize, dpos, csize)
	if src & 1:
		raise ValueError("Source must be 2-byte aligned")
	if dst & 1:
		raise ValueError("Destination must be 2-byte aligned")
	# note: ssize and dsize heights are ignored except for the checks

	cw, ch = csize

	cw = min(cw, dsize[0] - dpos[0])
	ch = min(ch, dsize[1] - dpos[1])
	cw = min(cw, ssize[0] - spos[0])
	ch = min(ch, ssize[1] - spos[1])

	if ssize[0] % 8:
		raise ValueError("Source width must be a multiple of 8")
	if dsize[0] % 8:
		raise ValueError("Dest width must be a multiple of 8")
	if autoalign:
		cw &= ~7
	else:
		if cw % 8:
			raise ValueError("Copy width must be a multiple of 8")
	
	
	regs.GFX_COPY_OP = 0
	regs.GFX_COPY_OP = 3
	
	# do the math FOR the engine because it's broken
	regs.GFX_COPY_SRC = (src>>1) + spos[0] + ssize[0] * spos[1]
	regs.GFX_COPY_DST = (dst>>1) + dpos[0] + dsize[0] * dpos[1]
	
	regs.GFX_COPY_SRC_WIDTH = ssize[0]
	regs.GFX_COPY_DST_WIDTH = dsize[0]
	
	regs.GFX_COPY_DST_COPY_WIDTH = cw
	regs.GFX_COPY_DST_COPY_HEIGHT = ch
	
	# these registers are useless and redundant and don't seem to matter
	regs.GFX_COPY_SRC_HEIGHT = ssize[1]
	regs.GFX_COPY_DST_HEIGHT = ssize[1]
	regs.GFX_COPY_SRC_COPY_WIDTH = csize[0]
	regs.GFX_COPY_SRC_COPY_HEIGHT =  csize[1]
	
	# these are redundant after adding them directly to the addresses
	# bonus: non multiples of 8 for X now work
	regs.GFX_COPY_SRC_X = 0
	regs.GFX_COPY_SRC_Y = 0
	regs.GFX_COPY_DST_X = 0
	regs.GFX_COPY_DST_Y = 0

	regs.GFX_COPY_START = 1
	while regs.GFX_COPY_FINISHED.val == 0:
		pass

#gfx_blit(TBIG, (240,320), (0,0), FBA, (240,320), (11,11), (240,320), autoalign=True)

def trailbounce():
	bw = 16
	bh = 16
	
	bx = 0
	by = 0
	
	spd = 2
	
	dbx = spd
	dby = spd

	while True:
		gfx_blit(TBIG, (240,320), (bx,by), FBA, (240,320), (bx,by), (bw, bh))
		regs.GFX_DRAW_START = 1

		bx += dbx
		by += dby
		if by+dby > (FB_HEIGHT - bh):
			dby = -spd
		if by+dby < 0:
			dby = spd
		if bx+dbx > (FB_WIDTH - bw):
			dbx = -spd
		if bx+dbx < 0:
			dbx = spd
		
		if (bx == 0 or bx == (FB_WIDTH - bw)) and (by == 0 or by == (FB_HEIGHT - bh)):
			gfx_blit(TBIG, (240,320), (bx,by), FBA, (240,320), (bx,by), (bw, bh))
			regs.GFX_DRAW_START = 1
			time.sleep(0)
			proxy.memset16(FBA, 0xF800,  320*240*2)

import random


def randomize(addr, l):
	for i in range(l):
		proxy.write8(addr+i, random.randint(0,255))

def rset(addr, v):
	for i,c in enumerate(v):
		proxy.write8(addr+i, c)

for i in range(127,256):
	#randomize(0x10007140, 1)
	#rset(0x10007140, [14, 13, 11, 9, 8, 7, 6, 5, 4, 10, 12, 1, 0, 0, 1, 3])
	#rset(0x10007140, [14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 3])
	proxy.write8(0x10007049, 0)
	proxy.memset16(FBA, 0xFFFF,  320*240*2)
	gfx_blit(TBIG, (240,320), (0,0), FBA, (240,320), (0,0), (240, 320))
	draw()



#trailbounce()

print "Done"
regs.GFX_DRAW_START = 1

