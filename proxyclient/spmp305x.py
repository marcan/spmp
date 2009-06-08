#!/usr/bin/python

import serial, os, struct, time, struct
from proxy import *
import initlib

uartdev = os.environ.get("SPMPDEVICE", "/dev/ttyUSB0")
uart = serial.Serial(uartdev, 115200)
uart.write("\0"*256)

iface = UartInterface(uart, debug=False)
proxy = SPMPProxy(iface, debug=False)

SCRATCH = 0x24700000
IO_BASE = 0x10000000

class AbstractRegister(object):
	def __init__(self, proxy, addr, cache=False):
		self.proxy = proxy
		self.addr = addr | IO_BASE
		self.cache = cache
		self._cv = None
		if self.addr % self.ALIGN:
			raise Exception("Unaligned register")
	
	def _gr(self):
		if self.cache and self._cv is not None:
			return self._cv
		self._cv = self.read()
		return self.read()
	def _gw(self, v):
		v &= self.MASK
		if self.cache and self._cv == v:
			return
		self._cv = v
		self.write(v)
	val = property(_gr, _gw)
	
	def __ior__(self, v):
		self.set(v & self.MASK)
		return self
	def __iand__(self, v):
		self.clear((v & self.MASK) ^ self.MASK)
		return self
	
	def set(self, v):
		self.val |= v
	def clear(self, v):
		self.val &= v ^ self.MASK
	def mask(self, clear, set):
		v = self.val
		v &= clear ^ self.MASK
		v |= set
		self.val = v
	
class R8(AbstractRegister):
	MASK = 0xFF
	ALIGN = 1
	def read(self):
		return self.proxy.read8(self.addr)
	def write(self, value):
		self.proxy.write8(self.addr, value)
	def set(self, value):
		self.proxy.set8(self.addr, value)
	def clear(self, value):
		self.proxy.clear8(self.addr,value)
	def mask(self, clear, set):
		self.proxy.mask8(self.addr, clear, set)

class R16(AbstractRegister):
	MASK = 0xFFFF
	ALIGN = 2
	def read(self):
		return self.proxy.read16(self.addr)
	def write(self, value):
		self.proxy.write16(self.addr, value)
	def set(self, value):
		self.proxy.set16(self.addr, value)
	def clear(self, value):
		self.proxy.clear16(self.addr,value)
	def mask(self, clear, set):
		self.proxy.mask16(self.addr, clear, set)

class R32(AbstractRegister):
	MASK = 0xFFFFFFFF
	ALIGN = 4
	def read(self):
		return self.proxy.read32(self.addr)
	def write(self, value):
		self.proxy.write32(self.addr, value)
	def set(self, value):
		self.proxy.set32(self.addr, value)
	def clear(self, value):
		self.proxy.clear32(self.addr,value)
	def mask(self, clear, set):
		self.proxy.mask32(self.addr, clear, set)

class U16(AbstractRegister):
	MASK = 0xFFFF
	ALIGN = 1
	def read(self):
		return self.proxy.read8(self.addr) | (self.proxy.read8(self.addr+1)<<8)
	def write(self, value):
		self.proxy.write8(self.addr, value & 0xFF)
		self.proxy.write8(self.addr+1, value >> 8)

class U24(AbstractRegister):
	MASK = 0xFFFFFF
	ALIGN = 1
	def read(self):
		return self.proxy.read8(self.addr) | (self.proxy.read8(self.addr+1)<<8) | \
			(self.proxy.read8(self.addr+2)<<16)
	def write(self, value):
		self.proxy.write8(self.addr, value & 0xFF)
		self.proxy.write8(self.addr+1, (value >> 8) & 0xFF)
		self.proxy.write8(self.addr+2, value >> 16)

class U32(AbstractRegister):
	MASK = 0xFFFFFFFF
	ALIGN = 1
	def read(self):
		return self.proxy.read8(self.addr) | (self.proxy.read8(self.addr+1)<<8) | \
			(self.proxy.read8(self.addr+2)<<16) | (self.proxy.read8(self.addr+3)<<24)
	def write(self, value):
		self.proxy.write8(self.addr, value & 0xFF)
		self.proxy.write8(self.addr+1, (value >> 8) & 0xFF)
		self.proxy.write8(self.addr+2, (value >> 16) & 0xFF)
		self.proxy.write8(self.addr+3, value >> 24)

def _reg(cls, addr, cache=False):
	reg = cls(proxy, addr, cache)
	def getreg(self):
		return reg
	def setreg(self,v):
		if v is reg:
			return
		reg.val = int(v)
	return property(getreg,setreg)

class Regs(object):
	LCD_DATA = _reg(R16, 0xA196)
	LCD_DATA_EXT = _reg(R8, 0xA0E4)
	LCD_CTRL = _reg(R8, 0xA195)
	LCD_DATA_DIR = _reg(R8, 0xA192)
	LCD_RESET_REG = _reg(R8, 0xA1B1)
	LCD_UPDATE = _reg(R8, 0xA00F)
	LCD_SCREEN_WIDTH = _reg(R16, 0xA1A0, True)
	LCD_SCREEN_HEIGHT = _reg(R16, 0xA1A2, True)
	LCD_SCREEN_T1 = _reg(R8, 0xA19E, True)
	LCD_SCREEN_T2 = _reg(R8, 0xA19F, True)
	
	GFX_DRAW_FROM_X1 = _reg(U16, 0xA141, True)
	GFX_DRWA_FROM_Y1 = _reg(U16, 0xA143, True)
	GFX_DRAW_FROM_X2 = _reg(U16, 0xA145, True)
	GFX_DRAW_FROM_Y2 = _reg(U16, 0xA147, True)
	GFX_DRAW_TO_X1 = _reg(U16, 0xA149, True)
	GFX_DRAW_TO_Y1 = _reg(U16, 0xA14b, True)
	GFX_DRAW_TO_X2 = _reg(U16, 0xA14d, True)
	GFX_DRAW_TO_Y2 = _reg(U16, 0xA14f, True)
	
	GFX_DRAW_STATUS = _reg(R8, 0x702E)
	GFX_DRAW_START = _reg(R8, 0x702F)
	GFX_COPY_FINISHED = _reg(R8, 0x7039)
	GFX_COPY_OP = _reg(R8, 0x703c, True)
	GFX_COPY_START = _reg(R8, 0x703f)
	GFX_COPY_BYTE_SIZE = _reg(R16, 0x7040, True)
	GFX_COPY_LSBS = _reg(R8, 0x7042, True) #000000DS (LSB from dest, src)
		
	GFX_BLEND_OUT_ADDR = _reg(R32, 0x7060, True)
	GFX_BLEND_FLAGS = _reg(R8, 0x7064, True)
	GFX_BLEND_MODE = _reg(R8, 0x7065, True)
	GFX_BLEND_FACTOR = _reg(R8, 0x7066, True)
	GFX_BLEND_SRC_DMASK_R = _reg(R8, 0x7067, True)
	GFX_BLEND_SRC_DMASK_G = _reg(R8, 0x7068, True)
	GFX_BLEND_SRC_DMASK_B = _reg(R8, 0x7069, True)
	GFX_BLEND_SRC_SMASK_R = _reg(R8, 0x706a, True)
	GFX_BLEND_SRC_SMASK_G = _reg(R8, 0x706b, True)
	GFX_BLEND_SRC_SMASK_B = _reg(R8, 0x706c, True)
	GFX_BLEND_DST_THRH_R = _reg(R8, 0x706d, True)
	GFX_BLEND_DST_THRH_G = _reg(R8, 0x706e, True)
	GFX_BLEND_DST_THRH_B = _reg(R8, 0x706f, True)
	GFX_BLEND_DST_THRL_R = _reg(R8, 0x7070, True)
	GFX_BLEND_DST_THRL_G = _reg(R8, 0x7071, True)
	GFX_BLEND_DST_THRL_B = _reg(R8, 0x7072, True)
	
	GFX_COPY_SRC_ADDR = _reg(R32, 0x70a0, True) #>>1
	GFX_COPY_SRC_WIDTH = _reg(R16, 0x70a4, True)
	GFX_COPY_SRC_HEIGHT = _reg(R16, 0x70a6, True)
	GFX_COPY_SRC_X = _reg(R16, 0x70a8, True)
	GFX_COPY_SRC_Y = _reg(R16, 0x70aa, True)
	GFX_COPY_SRC_COPY_WIDTH = _reg(R16, 0x70ac, True)
	GFX_COPY_SRC_COPY_HEIGHT = _reg(R16, 0x70ae, True)
	GFX_COPY_DST_ADDR = _reg(R32, 0x70b0, True) #>>1
	GFX_COPY_DST_WIDTH = _reg(R16, 0x70b4, True)
	GFX_COPY_DST_HEIGHT = _reg(R16, 0x70b6, True)
	GFX_COPY_DST_X = _reg(R16, 0x70b8, True)
	GFX_COPY_DST_Y = _reg(R16, 0x70ba, True)
	GFX_COPY_DST_COPY_WIDTH = _reg(R16, 0x70bc, True)
	GFX_COPY_DST_COPY_HEIGHT = _reg(R16, 0x70be, True)

	GFX_DRAW_SRC = _reg(R32, 0x7130, True)
	GFX_DRAW_SRC2 = _reg(R32, 0x7134, True)
	GFX_DRAW_WIDTH = _reg(R16, 0x7138, True)
	GFX_DRAW_HEIGHT = _reg(R16, 0x713A, True)

regs = Regs()
