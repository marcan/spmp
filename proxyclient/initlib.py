#!/usr/bin/python

import time

proxy = None
debug = False

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

def LCD_SetRegAddr(reg):
	if debug:
		print "ADDR 0x%x"%reg
	proxy.write16(LCD_DATA, reg)
	proxy.set8(LCD_DATA_DIR,LCD_OUT)
	proxy.write8(LCD_CTRL, LCD_CS)
	proxy.write8(LCD_CTRL, LCD_CS|LCD_WR)
	proxy.write8(LCD_CTRL, LCD_CS)
	proxy.write8(LCD_CTRL, LCD_CS|LCD_nRS)
	proxy.clear8(LCD_DATA_DIR,LCD_OUT)

def LCD_WriteRegData(data):
	if debug:
		print "DATA 0x%x"%data
	proxy.write16(LCD_DATA, data)
	proxy.set8(LCD_DATA_DIR,LCD_OUT)
	proxy.write8(LCD_CTRL, LCD_CS|LCD_nRS)
	proxy.write8(LCD_CTRL, LCD_CS|LCD_nRS|LCD_WR)
	proxy.write8(LCD_CTRL, LCD_CS|LCD_nRS)
	proxy.clear8(LCD_DATA_DIR,LCD_OUT)

def LCD_WriteReg(reg, data):
	LCD_SetRegAddr(reg)
	LCD_WriteRegData(data)

def delay(x):
	time.sleep(x/1000000.0)

