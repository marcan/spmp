#!/usr/bin/python

import serial, os, struct
from proxy import *

uartdev = os.environ.get("SPMPDEVICE", "/dev/ttyUSB0")
usbuart = serial.Serial(uartdev, 115200)

iface = UartInterface(usbuart, debug=False)
proxy = SPMPProxy(iface, debug=False)

SCRATCH = 0x24700000
REGS = int(sys.argv[1],0)
RSIZE = 0x600

proxy.memcpy8(SCRATCH, REGS, RSIZE)
origdump = iface.readmem(SCRATCH, RSIZE)
sys.stdout.write("\x1b[2J")
cx=0
while True:
	cx += 1
	print "\x1b[HIO register dump %d:"%cx
	proxy.memcpy8(SCRATCH, REGS, RSIZE)
	newdump = iface.readmem(SCRATCH, RSIZE)
	
	for i in range(0,len(newdump),32):
		sys.stdout.write("%08x "%(i+REGS))
		for w in range(0,32,4):
			for c in range(0,4):
				if origdump[i + w + c] != newdump[i + w + c]:
					sys.stdout.write("\x1b[1;4;31m%02x\x1b[m"%ord(newdump[i + w + c]))
				else:
					sys.stdout.write("%02x"%ord(newdump[i + w + c]))
			sys.stdout.write(" ")
		sys.stdout.write("   ")
		for w in range(0,32,4):
			for c in range(0,4):
					sys.stdout.write("%02x"%ord(origdump[i + w + c]))
			sys.stdout.write(" ")
		sys.stdout.write("\n")



