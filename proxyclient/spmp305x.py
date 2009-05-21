#!/usr/bin/python

import serial, os, struct, time, struct
from proxy import *
import initlib

uartdev = os.environ.get("SPMPDEVICE", "/dev/ttyUSB0")
uart = serial.Serial(uartdev, 115200)

iface = UartInterface(uart, debug=False)
proxy = SPMPProxy(iface, debug=False)

SCRATCH = 0x24700000
IO_BASE = 0x10000000

class AbstractRegister(object):
	def __init__(self, proxy, addr):
		self.proxy = proxy
		self.addr = addr | IO_BASE
		if self.addr % self.ALIGN:
			raise Exception("Unaligned register")
	
	def _gr(self):
		return self.read()
	def _gw(self, v):
		self.write(v & self.MASK)
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

def _reg(cls, addr):
	reg = cls(proxy, addr)
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
	LCD_SCREEN_WIDTH = _reg(R16, 0xA1A0)
	LCD_SCREEN_HEIGHT = _reg(R16, 0xA1A2)
	LCD_SCREEN_T1 = _reg(R8, 0xA19E)
	LCD_SCREEN_T2 = _reg(R8, 0xA19F)
	
	GFX_BLIT = _reg(R8, 0x702F)
	GFX_FB_START = _reg(R32, 0x7130)
	GFX_FB_END = _reg(R32, 0x7134)
	GFX_FB_WIDTH = _reg(R16, 0x7138)
	GFX_FB_HEIGHT = _reg(R16, 0x713A)
	GFX_BLIT_FROM_X1 = _reg(U16, 0xA141)
	GFX_BLIT_FROM_Y1 = _reg(U16, 0xA143)
	GFX_BLIT_FROM_X2 = _reg(U16, 0xA145)
	GFX_BLIT_FROM_Y2 = _reg(U16, 0xA147)
	GFX_BLIT_TO_X1 = _reg(U16, 0xA149)
	GFX_BLIT_TO_Y1 = _reg(U16, 0xA14b)
	GFX_BLIT_TO_X2 = _reg(U16, 0xA14d)
	GFX_BLIT_TO_Y2 = _reg(U16, 0xA14f)

regs = Regs()
