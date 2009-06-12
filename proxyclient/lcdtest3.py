#!/usr/bin/python

import serial, os, struct, time, struct, array
from proxy import *
import initlib

import spmp305x as spmp

import bunnygen
from numpy import *

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

init = 'init' in sys.argv[1:]
initlcd = 'initlcd' in sys.argv[1:]
upbig = 'upbig' in sys.argv[1:]
uptest = 'uptest' in sys.argv[1:]
upsma = 'upsma' in sys.argv[1:]
uptest2 = 'uptest2' in sys.argv[1:]
uptest2b = 'uptest2b' in sys.argv[1:]

if initlcd:
	regs.LCD_DATA_EXT = 0
	proxy.write32(0x10000008,0xFFFFFFFF)
	proxy.write32(0x10000110,0xFFFFFFFF)


if initlcd:
	proxy.set8(LCD_BASE, 1)
	regs.LCD_UPDATE = 1
	proxy.set8(LCD_BASE+0x1b9, 0x80)

	regs.LCD_RESET_REG &= ~LCD_RESET
	regs.LCD_RESET_REG |= LCD_RESET
	lcdinit.master_lcd_init(6)
else:
	initlib.LCD_SetRegAddr(0x22)

if init:
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

FBA = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)
FBB = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)
FBC = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)
FBD = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)

TBIG = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)
TTEST = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)
TSMALL = heap.malloc(160 * 120 * 2)
TBIGYUV = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)
TTEST2 = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)
TTEST2B = heap.malloc(LCD_WIDTH * LCD_HEIGHT * 2)

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

#proxy.memset16(FBA, 0xF800,  320*240*2)
#proxy.memset16(FBB, 0x001F,  320*240*2)

if init:
	setup_blit((0,0), (0,0), (240,320))

cfb = False

if upbig:
	setFB(TBIG, TBIG, (240,320))
	img = rgb2fb565("test.rgb")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TBIG+i, img[i:i+LCD_WIDTH*2])
		draw()
	proxy.dc_flushrange(TBIG, len(img))
	draw()
if uptest:
	setFB(TTEST, TTEST, (240,320))
	img = rgb2fb565("rgbtest.rgb")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TTEST+i, img[i:i+LCD_WIDTH*2])
		draw()
	proxy.dc_flushrange(TTEST, len(img))
	draw()
if uptest2:
	setFB(TTEST2, TTEST2, (240,320))
	img = rgba2fb4444("test2.rgba")
	for i in range(0,len(img),LCD_WIDTH*2):
		iface.writemem(TTEST2+i, img[i:i+LCD_WIDTH*2])
		draw()
	proxy.dc_flushrange(TTEST2, len(img))
	draw()
if upsma:
	img = rgb2fb565("test_small.rgb")
	for i in range(0,len(img),LCD_WIDTH):
		iface.writemem(TSMALL+i, img[i:i+LCD_WIDTH])
	proxy.dc_flushrange(TSMALL, len(img))

setFB(FBA, FBA, (240,320))
#draw()

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

import random

# GFX STUFF

class GraphicsEngine(object):
	ROP_BLACKNESS = 0x00
	ROP_SRC = 0xCC
	ROP_DST = 0xAA
	ROP_PEN = 0xF0
	ROP_WHITENESS = 0xFF
	def __init__(self):
		self.fifo = []
		self.regs = [None] * 0x1d
		self.reg_cur = [None] * 0x1d
		self.hw_tail = 0
		self.fcmds = 0
		self.regs[0xd] = self.ROP_SRC

	def initialize(self):
		print "2D init"
		proxy.write8(0x1000c007, 1)
		self.wait()
		self.hw_tail = proxy.read8(0x1000c018)
		print "hw tail: 0x%02x"%self.hw_tail
		proxy.gfx_init()

	def wait(self):
		#print "Wait for 2D engine"
		while proxy.read8(0x1000c015) & 1:
			pass
	
	def _push16(self, v):
		#print "===> Push word %04x"%v
		proxy.write8(0x1000c000, v & 0xFF)
		proxy.write8(0x1000c000, v >> 8)
	
	def send_pending(self):
		if not self.fifo:
			return
		print "Flushing gfx FIFO: [%s]"%', '.join(["%04x"%x for x in self.fifo])
		d = ''.join([struct.pack("<H", x) for x in self.fifo])
		iface.writemem(SCRATCH, d)
		#proxy.memcpy16(SCRATCH+len(d),SCRATCH,len(d))
		p = SCRATCH+len(d)
		for i in range(8):
			proxy.memcpy8(p,SCRATCH,len(d))
			p += len(d)
		print "RENDER START %d"%(len(d))
		hwt = proxy.read8(0x1000c018)
		print "hw tail: 0x%02x"%hwt
		mul = 1
		self.fcmds *= mul
		print "expected: 0x%02x"%((hwt+self.fcmds)&0xff)
		t1 = time.time()
		proxy.gfx_sendfifo(SCRATCH, len(self.fifo)*mul)
		t2 = time.time()
		proxy.nop()
		t3 = time.time()
		print "hw tail: 0x%02x"%proxy.read8(0x1000c018)
		self.fcmds = 0
		print "RENDER END"
		noptime = t3 - t2
		rtime = 2 * t2 - t1 - t3
		print "Render time: %.04f seconds"%rtime
		self.fifo = []
		return
		pending = False
		while self.fifo:
			hw_head = proxy.read8(0x1000c018)
			fifo_free = 28 - ((self.hw_tail - proxy.read8(0x1000c018)) & 0xFF)
			#print "tail: 0x%02x, head: 0x%02x, fifo_free: %d"%(self.hw_tail, hw_head, fifo_free)
			cval = self.fifo.pop(0)
			print "==> Control word: %04x"%cval
			count = cval >> 8
			reg = cval & 0xFF
			if fifo_free < count:
				print "Waiting for GFX engine"
				while fifo_free < count:
					fifo_free = 28 - ((self.hw_tail - proxy.read8(0x1000c018)) & 0xFF)
			if count == 0:
				cword = 0x2d00 | reg
			else:
				cword = 0x4040 | (count << 8) | reg
			proxy.write8(0x1000c010, 1)
			proxy.write8(0x1000c006, 0)
			proxy.write8(0x1000c001, 1)
			self._push16(cword)
			for i in range(count+1):
				self._push16(self.fifo.pop(0))
			self.hw_tail = (self.hw_tail + count + 1) & 0xFF
	
	def flush_settings(self):
		self.draw(None)
	
	def draw(self, value):
		if value is not None:
			self.regs[0x1c] = value
		dirty = [a != b for a,b in zip(self.regs, self.reg_cur)]
		self.reg_cur = list(self.regs)
		if value is not None:
			dirty[0x1c] = True
		lp = None
		for i in range(0x1d):
			if lp is None:
				if dirty[i]:
					lp = i
			else:
				if not dirty[i]:
					cnt = i - lp
					self.fifo += [((cnt-1)<<8) | lp] + self.regs[lp:i]
					self.fcmds += cnt
					dirty = dirty[:lp] + [False]*(i-lp) + dirty[i:]
					lp = None
		i = 0x1d
		if lp is not None:
			cnt = i - lp
			self.fifo += [((cnt-1)<<8) | lp] + self.regs[lp:i]
			self.fcmds += cnt
			dirty = dirty[:lp] + [False]*(i-lp) + dirty[i:]
			lp = None
			

	def setROP(self, rop):
		self.regs[0xd] &= 0xFF00
		self.regs[0xd] |= rop
	
	def setPenColor(self, col):
		self.regs[0x0e] = col
	
	def setFB(self, fb, w, h):
		self.regs[0x05] = fb & 0xFFFF
		self.regs[0x06] = fb >> 16
		self.regs[0x07] = w << 1
		self.regs[0x08] = h
	
	def fill(self, color, x, y, w, h):
		self.setPenColor(color)
		self.regs[0x09] = x
		self.regs[0x0a] = y
		self.regs[0x0b] = w
		self.regs[0x0c] = h
		self.draw(0x0000)
	
	SHADE_FLAG_FLIP_V = 0x100
	SHADE_FLAG_FLIP_H = 0x200
	SHADE_FLAG_V = 0x400
	SHADE_FLAG_H = 0x800
	
	def shade(self, color, x, y, w, h, xcol=None, ycol=None, xflip=False, yflip=False):
		self.setPenColor(color)
		flags = 3
		if xcol is not None:
			self.regs[0x0f] = xcol[0]
			self.regs[0x10] = xcol[1]
			self.regs[0x11] = xcol[2]
			flags |= SHADE_FLAG_H
			if xflip:
				flags |= SHADE_FLAG_FLIP_H
		if ycol is not None:
			self.regs[0x12] = ycol[0]
			self.regs[0x13] = ycol[1]
			self.regs[0x14] = ycol[2]
			flags |= SHADE_FLAG_V
			if yflip:
				flags |= SHADE_FLAG_FLIP_V
		self.regs[0x09] = x
		self.regs[0x0a] = y
		self.regs[0x0b] = w
		self.regs[0x0c] = h
		self.draw(flags | 0x10)
	
	BLIT_FLAG_BITPLANE_MASK = 0x8000
	BLIT_FLAG_STIPPLE = 0x800
	BLIT_FLAG_LOAD_PALETTE = 0x400
	BLIT_FLAG_IDX4 = 0x300
	BLIT_FLAG_IDX8 = 0x200
	BLIT_FLAG_RGB4444 = 0x100
	BLIT_FLAG_RGB565 = 0x000
	BLIT_FLAG_BLEND = 0x80
	BLIT_FLAG_DIM_DST = 0x4000
	BLIT_FLAG_TRANSFORM = 0x10
	
	# note: transform breaks sx, sy
	
	TRANSFORM_ROT90 = 0x1000
	TRANSFORM_ROT180 = 0x2000
	TRANSFORM_XFLIP = 0x4000
	
	def blit(self, src, stride, sx, sy, dx, dy, w, h):
		flags = 0
		self.regs[0x0] = src & 0xFFFF
		self.regs[0x1] = src >> 16
		self.regs[0x2] = stride
		self.regs[0x3] = sx
		self.regs[0x4] = sy
		self.regs[0x9] = dx
		self.regs[0xa] = dy
		self.regs[0xb] = w
		self.regs[0xc] = h
		self.regs[0xd] &= 0x00FF
		self.regs[0xd] |= 0x2000
		self.regs[0xf] = 0x0000
		self.regs[0x10] = 0x0000
		self.regs[0x11] = 0x0000
		self.regs[0x12] = 0x0000
		self.regs[0x13] = TBIG & 0xFFFF
		self.regs[0x14] = TBIG >> 16
		self.regs[0x15] = 0xffff
		self.regs[0x16] = 0xffff
		self.regs[0x17] = 0xffff
		self.regs[0x18] = 0xffff
		self.regs[0x19] = 0xffff
		self.regs[0x20] = 0xffff
		self.regs[0x21] = 0xffff
		self.regs[0x22] = 0xffff
		#self.write(0x2a, random.randint(0,0xffff), 0)
		#self.write(0x2c, random.randint(0,0xffff), 0)
		#self.write(0x2e, random.randint(0,0xffff), 0)
		#self.write(0x30, random.randint(0,0xffff), 0)
		bl = 0x0000
		bl |= 0x0808
		bl |= 0x0000
		self.regs[0x19] = bl
		#self.write(0x32, random.randint(0,0xffff), 0) # 0x80 mask
		#self.write(0x34, random.randint(0,0xffff), 0)
		#self.write(0x34, 0x001f, 0) # bitplane mask
		#self.write(0x32, 0xffff, 0)
		#self.write(0x36, random.randint(0,0xffff), 0)
		#self.write(0x38, 0x8054, 0) #!!!
		#flags |= 0x4000 #DIM_DST
		flags |= 0x2000
		#flags |= 0x1000 # death
		#flags |= 0x100
		#flags |= 0x0080
		flags |= 0x0040
		flags |= 0x0020
		#flags |= 0x0010
		flags |= 0x0008
		flags |= 0x0004
		self.draw(flags)
		#self.write(0x38, random.randint(0,0xffff) & 0x706C, 0)
	
	LINE_FLAG_STYLED = 0x800
	LINE_FLAG_STYLE_RESET = 0x200
	
	def line(self, color, sx, sy, dx, dy, pattern=None, patreset=True):
		flags = 2
		self.setPenColor(color)
		self.regs[0x3] = sx
		self.regs[0x4] = sy
		self.regs[0x9] = dx
		self.regs[0xa] = dy
		if pattern is not None:
			assert 0 < len(pattern) <= 64
			flags |= 0x800
			if patreset:
				flags |= 0x200
			self.regs[0xc] = len(pattern) - 1
			pv = 0
			for i,v in enumerate(pattern):
				if v and v != "0":
					pv |= (1<<i)
			self.regs[0x0f] = pv & 0xFFFF
			if len(pattern) > 16:
				self.regs[0x10] = (pv>>16) & 0xFFFF
			if len(pattern) > 32:
				self.regs[0x11] = (pv>>32) & 0xFFFF
			if len(pattern) > 48:
				self.regs[0x12] = (pv>>48) & 0xFFFF
		self.draw(flags)
	
	def dirty_regs(self, regs):
		for r in regs:
			self.reg_cur[r] = None

def rgb565(r,g,b):
	r >>= 1;
	b >>= 1
	return (r<<11) | (g<<5) | b


#gfx_blit(TBIG, (240,320), (0,0), FBA, (240, 320), (0,0), (240, 320))
#draw()

gfx = GraphicsEngine()

gfx.initialize()
gfx.setFB(FBA, 240, 320)
gfx.flush_settings()
gfx.send_pending()



#gfx.setROP(gfx.ROP_SRC)
#

gfx.setROP(gfx.ROP_PEN)
gfx.fill(rgb565(20,20,40), 0, 0, 240, 320)
gfx.send_pending()
gfx.wait()
draw()
time.sleep(1)

xr = 0
yr = 0

lpats = [
	(1, 0b1),
	(2, 0b01),
	(3, 0b001),
	(4, 0b0001),
	(3, 0b001),
	(2, 0b01),
	(1, 0b1),
]

frame = 0
lpi = 0

proxy.set_render_style(*lpats[0])


proxy.set_render_colors(0xffff, rgb565(20,20,40))

lt = time.time()

while True:
	#gfx.setROP(gfx.ROP_PEN)
	#gfx.fill(0xf800, 0, 0, 240, 320)
	##gfx.setPenColor(0xffff)
	##gfx.flush_settings()
	#print "Fill and set"
	#gfx.send_pending()
	#gfx.wait()
	#print "FS done"
	#draw()
	
	if frame%50 == 49:
		lpi = (lpi + 1)%len(lpats)
		n,v = lpats[lpi]
		proxy.set_render_style(n,v)
	
	m = identity(3)
	m = dot([[1,0,0],[0,1,0],[0,0,-1]],m)
	m = dot([[0.9,0,0],[0,0.9,0],[0,0,0.9]],m)
	m = dot(bunnygen.yrot(yr),m)
	m = dot(bunnygen.xrot(math.sin(xr) * 0.7),m)
	
	mat = struct.pack("<iii", *[int(i*65536) for i in m[0]])
	mat += struct.pack("<iii", *[int(i*65536) for i in m[1]])
	mat += struct.pack("<iii", *[int(i*65536) for i in m[2]])
	#print "Upload matrix"
	iface.writemem(SCRATCH, mat)
	#print "Render bunny"
	proxy.render_bunny(SCRATCH)
	#print "Bunny render done"
	#gfx.dirty_regs([3,4,9,10,14])
	#print "Wait"
	gfx.wait()
	#print "Draw"
	draw()
	#print "Draw done"
	yr -= 0.06
	xr += 0.08
	
	if frame%6 == 5:
		ct = time.time()
		et = ct - lt
		print "FPS: %.2f"%(6.0/et)
		lt = ct
	
	frame += 1

sys.exit(1)

#for i in range(-120,120,1):
	#gfx.setROP(gfx.ROP_PEN)
	#gfx.line(0xf800, 120, 10, 120 + i, 320)
	#gfx.send_pending()
	#gfx.wait()
	#draw()
	#pass

lines = bunnygen.gen(0,0,0)
print "Linecount:",len(lines)
gfx.setROP(gfx.ROP_PEN)
for i,l in enumerate(lines):
	(y1,x1),(y2,x2) = l
	x1,y1,x2,y2 = map(int, (x1,y1,x2,y2))
	gfx.line(0xffff, x1,y1,x2,y2)
		#gfx.send_pending()
		#gfx.wait()
		#draw()
		#print "%d/%d"%(i,len(lines))
		#time.sleep(1)
gfx.send_pending()
gfx.wait()
draw()


sys.exit(1)


#gfx.send_pending()
#gfx.wait()
#draw()
##time.sleep(1)
#gfx.fill(0xffe0, 0, 0, 10, 10)
#gfx.send_pending()
#gfx.wait()
#draw()
#gfx.fill(0xffe0, 230, 0, 10, 10)
#gfx.send_pending()
#gfx.wait()
#draw()
#gfx.fill(0xffe0, 230, 310, 10, 10)
#gfx.send_pending()
#gfx.wait()
#draw()
#gfx.fill(0xffe0, 0, 310, 10, 10)
#gfx.send_pending()
#gfx.wait()
#draw()
gfx.setROP(gfx.ROP_SRC)
gfx.blit(TTEST2,480,0,0,0,0,240,320)
gfx.send_pending()
gfx.wait()
draw()

gfx.setROP(gfx.ROP_PEN)

import math

i = 1

for a in range(5):
	phi = a * (360/32.0) * math.pi / 180.0
	phi2 = (a+1) * (360/32.0) * math.pi / 180.0
	x = math.cos(phi) * 100
	y = math.sin(phi) * 100
	xn = math.cos(phi2) * 100
	yn = math.sin(phi2) * 100
	ib = i / 2
	ia = (i + 1) / 2
	gfx.line(0xffff, 120, 160, int(x) + 120, int(y) + 160, "1"*ia + "0"*ib)
	gfx.send_pending()
	gfx.wait()
	draw()
	gfx.line(0x07ff, int(x) + 120, int(y) + 160, int(xn) + 120, int(yn) + 160)
	gfx.send_pending()
	gfx.wait()
	draw()
	if a < 16:
		i += 1
	else:
		i -= 1

time.sleep(1)
gfx.setROP(gfx.ROP_PEN ^ gfx.ROP_DST)
gfx.fill(0xf800, 0, 0, 240, 320)
gfx.send_pending()
gfx.wait()
draw()

time.sleep(1)
gfx.setROP(gfx.ROP_PEN ^ gfx.ROP_DST)
gfx.fill(0xf800, 0, 0, 240, 320)
gfx.send_pending()
gfx.wait()
draw()

time.sleep(1)
gfx.setROP(gfx.ROP_PEN | gfx.ROP_DST)
gfx.fill(0x001f, 0, 0, 240, 320)
gfx.send_pending()
gfx.wait()
draw()

time.sleep(1)
gfx.setROP((~gfx.ROP_PEN) & gfx.ROP_DST)
gfx.fill(0x001f, 0, 0, 240, 320)
gfx.send_pending()
gfx.wait()
draw()

time.sleep(1)
gfx.setROP(gfx.ROP_PEN | gfx.ROP_DST)
gfx.fill(0x07e0, 0, 0, 240, 320)
gfx.send_pending()
gfx.wait()
draw()

time.sleep(1)
gfx.setROP((~gfx.ROP_PEN) & gfx.ROP_DST)
gfx.fill(0x07e0, 0, 0, 240, 320)
gfx.send_pending()
gfx.wait()
draw()

time.sleep(1)
gfx.setROP(gfx.ROP_SRC | gfx.ROP_DST)
gfx.blit(TBIG,480,0,0,0,0,240,320)
gfx.send_pending()
gfx.wait()
draw()
