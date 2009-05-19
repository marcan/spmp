#!/usr/bin/python

import serial, os, struct, code, traceback, readline
from proxy import *
import __main__
import __builtin__

saved_display = sys.displayhook

def display(val):
	global saved_display
	if isinstance(val, int) or isinstance(val, long):
		__builtin__._ = val
		print hex(val)
	else:
		saved_display(val)

sys.displayhook = display

# convenience
h = hex

uartdev = os.environ.get("SPMPDEVICE", "/dev/ttyUSB0")
usbuart = serial.Serial(uartdev, 115200)

iface = UartInterface(usbuart, debug=False)
proxy = SPMPProxy(iface, debug=False)

SCRATCH = 0x11000000

locals = __main__.__dict__

for attr in dir(iface):
	locals[attr] = getattr(iface,attr)
for attr in dir(proxy):
	locals[attr] = getattr(proxy,attr)
del attr

from armutils import *

class ConsoleMod(code.InteractiveConsole):
	def showtraceback(self):
		type, value, tb = sys.exc_info()
		self.write(traceback.format_exception_only(type, value)[0])

ConsoleMod(locals).interact("Have fun!")

