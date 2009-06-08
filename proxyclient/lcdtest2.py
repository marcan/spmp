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

def rgba2fb1555(fname):
	rgbd = open(fname, "rb").read()
	do = ""
	l = len(rgbd) / 4
	for i in xrange(l):
		r,g,b,a = map(ord, rgbd[i*4:i*4+4])
		r >>= 3
		g >>= 3
		b >>= 3
		val = r<<10 | g<<5 | b
		if a >= 0x80:
			val |= 0x8000
		do += struct.pack("<H", val)
	return do

def rgba2fb4444(fname):
	rgbd = open(fname, "rb").read()
	do = ""
	l = len(rgbd) / 4
	for i in xrange(l):
		r,g,b,a = map(ord, rgbd[i*4:i*4+4])
		r >>= 4
		g >>= 4
		b >>= 4
		a >>= 4
		val = a<<12 | r<<8 | g<<4 | b
		do += struct.pack("<H", val)
	return do

def toyuv(r,g,b):
	y =  0.299 * r +0.587 * g +0.144 * b
	u = -0.169 * r -0.331 * g +0.499 * b
	v =  0.499 * r -0.418 * g +0.0813* b
	return y,u,v

def clamp(x):
	x = int(x+0.5)
	if x < 0:
		return 0
	if x > 255:
		return 255
	return x

def rgb2yuv(fname):
	rgbd = open(fname, "rb").read()
	do = ""
	l = len(rgbd) / (3*8)
	for i in xrange(l):
		yb = ""
		ub = ""
		vb = ""
		for p in range(4):
			y1,u1,v1 = toyuv(*map(ord, rgbd[i*24+p*6+0:i*24+p*6+3]))
			y2,u2,v2 = toyuv(*map(ord, rgbd[i*24+p*6+3:i*24+p*6+6]))
			
			y1 = clamp(y1)
			y2 = clamp(y2)
			u = clamp((u1 + u2) / 2 + 128)
			v = clamp((v1 + v2) / 2 + 128)
			
			yb += struct.pack("BB", y1, y2)
			ub += struct.pack("B", u)
			vb += struct.pack("B", v)
		do += yb + ub + vb
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
upbigyuv = 'upbigyuv' in sys.argv[1:]
uptest2 = 'uptest2' in sys.argv[1:]
uptest2b = 'uptest2b' in sys.argv[1:]

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

TBIG = FBB + (LCD_WIDTH * LCD_HEIGHT * 2)
TTEST = TBIG + (LCD_WIDTH * LCD_HEIGHT * 2)
TSMALL = TTEST + (LCD_WIDTH * LCD_HEIGHT * 2)
FBC = TSMALL + (120*160*2)
TBIGYUV = FBC + (LCD_WIDTH * LCD_HEIGHT * 2)
TTEST2 = TBIGYUV + (LCD_WIDTH * LCD_HEIGHT * 2)
TTEST2B = TTEST2 + (LCD_WIDTH * LCD_HEIGHT * 2)
FBD = TTEST2B + (LCD_WIDTH * LCD_HEIGHT * 2)

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

proxy.memset16(FBA, 0xF800,  320*240*2)
#proxy.memset16(FBB, 0x001F,  320*240*2)

setup_blit((0,0), (0,0), (240,320))

cfb = False

if upbig:
	setFB(TBIG, TBIG, (240,320))
	img = rgb2fb565("test.rgb")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TBIG+i, img[i:i+LCD_WIDTH*2])
		draw()
if upbigyuv:
	setFB(TBIGYUV, TBIG, (240,320))
	img = rgb2yuv("test.rgb")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TBIGYUV+i, img[i:i+LCD_WIDTH*2])
		draw()
if uptest:
	setFB(TTEST, TTEST, (240,320))
	img = rgb2fb565("rgbtest.rgb")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TTEST+i, img[i:i+LCD_WIDTH*2])
		draw()
if uptest2:
	setFB(TTEST2, TTEST2, (240,320))
	img = rgba2fb1555("test2.rgba")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TTEST2+i, img[i:i+LCD_WIDTH*2])
		draw()
if uptest2b:
	setFB(TTEST2B, TTEST2B, (240,320))
	img = rgba2fb4444("test2.rgba")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TTEST2B+i, img[i:i+LCD_WIDTH*2])
		draw()
if upsma:
	img = rgb2fb565("test_small.rgb")
	for i in range(0,len(img),LCD_WIDTH):
		iface.writemem(TSMALL+i, img[i:i+LCD_WIDTH])

setFB(FBA, FBA, (240,320))
#draw()

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

def gfx_blit(src, ssize, spos, dst, dsize, dpos, csize, op=3, autoalign=False):
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
	regs.GFX_COPY_OP = op
	
	# do the math FOR the engine because it's broken
	regs.GFX_COPY_SRC_ADDR = (src>>1) + spos[0] + ssize[0] * spos[1]
	regs.GFX_COPY_DST_ADDR = (dst>>1) + dpos[0] + dsize[0] * dpos[1]
	
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

BLEND_SRC_RGB565 = 0
BLEND_SRC_ARGB1555 = 8
BLEND_SRC_ARGB4444 = 16

def gfx_set_blend_src_fmt(fmt):
	regs.GFX_BLEND_FLAGS = 1 | 2 | 4 | fmt

def gfx_set_blend_dmask(r, g, b):
	fmt = regs.GFX_BLEND_FLAGS.val & 24
	if fmt == 0:
		regs.GFX_BLEND_SRC_DMASK_R = r & 0xf8
		regs.GFX_BLEND_SRC_DMASK_G = g & 0xfc
		regs.GFX_BLEND_SRC_DMASK_B = b & 0xf8
	elif fmt == 8:
		regs.GFX_BLEND_SRC_DMASK_R = r & 0xf8
		regs.GFX_BLEND_SRC_DMASK_G = g & 0xf8
		regs.GFX_BLEND_SRC_DMASK_B = b & 0xf8
	elif fmt == 16:
		regs.GFX_BLEND_SRC_DMASK_R = (r & 0xf0) | (r >> 4)
		regs.GFX_BLEND_SRC_DMASK_G = (g & 0xf0) | (g >> 4)
		regs.GFX_BLEND_SRC_DMASK_B = (b & 0xf0) | (b >> 4)

def gfx_set_blend_smask(r, g, b):
	fmt = regs.GFX_BLEND_FLAGS.val & 24
	if fmt == 0:
		regs.GFX_BLEND_SRC_SMASK_R = r & 0xf8
		regs.GFX_BLEND_SRC_SMASK_G = g & 0xfc
		regs.GFX_BLEND_SRC_SMASK_B = b & 0xf8
	elif fmt == 8:
		regs.GFX_BLEND_SRC_SMASK_R = r & 0xf8
		regs.GFX_BLEND_SRC_SMASK_G = g & 0xf8
		regs.GFX_BLEND_SRC_SMASK_B = b & 0xf8
	elif fmt == 16:
		regs.GFX_BLEND_SRC_SMASK_R = (r & 0xf0) | (b >> 4)
		regs.GFX_BLEND_SRC_SMASK_G = (g & 0xf0) | (b >> 4)
		regs.GFX_BLEND_SRC_SMASK_B = (b & 0xf0) | (b >> 4)

def gfx_set_blend_thresh(rl, gl, bl, rh, gh, bh):
	regs.GFX_BLEND_DST_THRH_R = rh
	regs.GFX_BLEND_DST_THRH_G = gh
	regs.GFX_BLEND_DST_THRH_B = bh
	regs.GFX_BLEND_DST_THRL_R = rl
	regs.GFX_BLEND_DST_THRL_G = gl
	regs.GFX_BLEND_DST_THRL_B = bl

def gfx_blend(src, dst, out, size, mode, factor=0x20):
	print "blend %08x %08x %08x %r %d %d"%(src, dst, out, size, mode, factor)
	if src & 1:
		raise ValueError("Source must be 2-byte aligned")
	if dst & 1:
		raise ValueError("Destination must be 2-byte aligned")
	if out & 1:
		raise ValueError("Output must be 2-byte aligned")
	
	if size[0] % 8:
		raise ValueError("Width must be a multiple of 8")
	
	regs.GFX_COPY_OP = 0
	regs.GFX_COPY_OP = 14
	regs.GFX_BLEND_MODE = mode
	regs.GFX_BLEND_FACTOR = factor
	
	# do the math FOR the engine because it's broken
	regs.GFX_COPY_SRC_ADDR = (src>>1)
	regs.GFX_COPY_DST_ADDR = (dst>>1)
	regs.GFX_BLEND_OUT_ADDR = (out>>1)

	regs.GFX_COPY_SRC_WIDTH, regs.GFX_COPY_SRC_HEIGHT = size
	regs.GFX_COPY_SRC_COPY_WIDTH, regs.GFX_COPY_SRC_COPY_HEIGHT = size
	regs.GFX_COPY_DST_WIDTH, regs.GFX_COPY_DST_HEIGHT = size
	regs.GFX_COPY_DST_COPY_WIDTH, regs.GFX_COPY_DST_COPY_HEIGHT = size
	
	regs.GFX_COPY_SRC_X = 0
	regs.GFX_COPY_SRC_Y = 0
	regs.GFX_COPY_DST_X = 0
	regs.GFX_COPY_DST_Y = 0

	regs.GFX_COPY_START = 1
	while regs.GFX_COPY_FINISHED.val == 0:
		pass

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

def set_7065_thru_7072(thr, thg, thb, tlr, tlg, tlb, mr, mg, mb, smr, smg, smb, mode, fact):
	regs.GFX_BLEND_MODE = mode
	regs.GFX_BLEND_FACTOR = fact
	regs.GFX_BLEND_SRC_DMASK_R = mr
	regs.GFX_BLEND_SRC_DMASK_G = mg
	regs.GFX_BLEND_SRC_DMASK_B = mb
	regs.GFX_BLEND_SRC_SMASK_R = smr
	regs.GFX_BLEND_SRC_SMASK_G = smg
	regs.GFX_BLEND_SRC_SMASK_B = smb
	regs.GFX_BLEND_DST_THRH_R = thr
	regs.GFX_BLEND_DST_THRH_G = thg
	regs.GFX_BLEND_DST_THRH_B = thb
	regs.GFX_BLEND_DST_THRL_R = tlr
	regs.GFX_BLEND_DST_THRL_G = tlg
	regs.GFX_BLEND_DST_THRL_B = tlb

def setstuff(a,b,c,d):	
	a &= 0xf8
	b &= 0xf8
	c &= 0xf8
	
	print hex(a),hex(b),hex(c),hex(d)

	set_7065_thru_7072(00,00,00,0,110,110, a, b, c, 0xff,0xff,0xff, 1, d)

# blend modes

# COLOR MASK modes: if src color matches Dmask, then OUT = DST always.
#                   if src color matches Smask, then OUT = SRC always.
# DEST THRESH modes: if dest color components are > threshl and < threshh, then color is replaced with black
#                    THIS APPLIES BEFORE BLENDING AND AFFECTS THE DST COLOR IN THE EQUATION

BLEND_MODE_DST = 0
BLEND_MODE_SRC = 1
BLEND_MODE_MASK_ALPHA = 2
BLEND_MODE_MASK_ADD = 3
BLEND_MODE_MASK_SUB = 4
BLEND_MODE_MASK_ADD25 = 5
BLEND_MODE_SRC2 = 6
BLEND_MODE_THRESH_ADD = 7
BLEND_MODE_THRESH_SUB = 8
BLEND_MODE_THRESH_ADD25 = 9

# 0 = DEST
# 1 = SOURCE
# 2 = COLOR MASK and
#	IF SRC & 0x8000 = 0:
#		OUT = SRC * (1-BLEND_FACTOR) + DST * BLEND_FACTOR
#	ELSE:
#		OUT = SRC
# 3 = COLOR MASK and ADD
#	IF SRC & 0x8000 = 0:
#		OUT = CLAMP(SRC + DST)
#	ELSE:
#		OUT = SRC
# 4 = COLOR MASK and SUBTRACT
#	IF SRC & 0x8000 = 0:
#		OUT = CLAMP(DST - SRC)
#	ELSE:
#		OUT = SRC
# 5 = COLOR MASK and ADD 25%
#	IF SRC & 0x8000 = 0:
#		OUT = CLAMP(0.25*SRC + DST)
#	ELSE:
#		OUT = SRC
# 6 = SOURCE
# 7 = DEST THRESH:
#		OUT = CLAMP(SRC + DST)
# 8 = DEST THRESH before and then:
#	IF DST == 0 (or within threshold and clamped to 0):
#		OUT = SRC
#	ELSE:
#		OUT = CLAMP(DST - SRC)
# 9 = DEST THRESH before and then ADD 25%:
#	IF DST == 0 (or within threshold and clamped to 0):
#		OUT = SRC
#	ELSE:
#		OUT = CLAMP(0.25 * SRC + DST)
#   
# 10+ = BLACKNESS

#gfx_blit(TTEST, (240,320), (0,0), FBA, (240,320), (0,0), (240, 320))
#draw()
#time.sleep(0.1)
#gfx_blit(TBIG, (240,320), (0,0), FBA, (240,320), (0,0), (240, 320))
#draw()
#time.sleep(0.1)
#gfx_blit(TSMALL, (120,160), (0,0), FBA, (240,320), (0,0), (240, 320))
#draw()
#time.sleep(0.1)

#proxy.memset16(FBA, 0x001F,  320*240*2)
#draw()

#proxy.memset32(FBC,         0x0000ffff, 320*240)
#proxy.memset32(FBC+320*240, 0xffff0000, 320*240)

#d = struct.pack(">IIII", 0xffffffff, 0xffffffff, 0x80808080, 0x80808080)

#d *= 60

#iface.writemem(FBC, d * 8)
proxy.write8(0x10007049, 0)
regs.GFX_BLEND_OUT_ADDR = FBA>>1
proxy.write8(0x10007064, 1 | 2 | 4 | 8)

blends = [
	(10,20,30),
	(255,0,0), (0,255,0), (0,0,255), (255,255,255),
	(0,255,255), (255,0,255), (255,255,0), (0,0,0),
	(127,255,127)
]

proxy.memcpy32(FBC, TTEST2B, 320*240*2)
proxy.memset32(FBD, 0x00000000, 320*240*2)

d = struct.pack(">IIII", 0x00000000, 0x00000000, 0x00000000, 0x00000000)

iface.writemem(FBD, d * 240)

gfx_set_blend_src_fmt(BLEND_SRC_ARGB4444)

for r,g,b in blends:
	gfx_set_blend_dmask(r,g,b)
	gfx_blend(TBIGYUV, FBC, FBA, (240,320), BLEND_MODE_MASK_ALPHA, 0)
	draw()
	time.sleep(0.2)

gfx_set_blend_smask(255,255,255)

proxy.memcpy32(FBC, TTEST2, 320*240*2)

for i in range(0,0x21):
	gfx_blend(TBIGYUV, FBC, FBA, (240,320), BLEND_MODE_MASK_ALPHA, i)
	draw()

