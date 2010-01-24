#!/usr/bin/python

import serial, os, struct, time, struct, array
from proxy import *
import initlib

import spmp305x as spmp

import malloc

iface = spmp.iface
proxy = spmp.proxy
regs = spmp.regs

heap = malloc.Heap(0x24200000, 0x24700000)

SCRATCH = heap.malloc(1024*1024)

print "USB test"

# usbInit
proxy.write8(0x10005031, 1)
proxy.write8(0x10005236, 1)
proxy.write8(0x10005360, 0x00),
proxy.write8(0x10005361, 0x06),
proxy.write8(0x10005362, 0x1f),
proxy.write8(0x10005363, 0x00),

# hwUsbInit
proxy.write8(0x100000e5, 0)
proxy.write8(0x10005023, 1)
proxy.write8(0x10005031, 1)
proxy.write8(0x10005236, 1)

if proxy.read8(0x100000b1) & 0x20:
	proxy.write8(0x10005022, 1)

# usbInit Enter CHIP
proxy.write8(0x10005004, 0)
proxy.write8(0x100050a0, 0)

proxy.write8(0x100050d0, 1)

# insert loop
proxy.set8(0x10001347, 1)

# enable inputs for pull-up and detect pin (normal GPIO register)
proxy.set8(0x100001ee, 0x18)

# these are GPIO19 and 20, why are they controlled here and not in the normal GPIO register range?!?
# disable pull-up
proxy.write8(0x10005310, 0x00)
proxy.write8(0x10005311, 0x02)

# wait for usb to be connected
# checking normal GPIO register would also work
while True:
	# do some debouncing
	for i in range(20):
		if not proxy.read8(0x10005312) & 1:
			break
	else:
		break

print "USB Connected"
# enable pull-up to signal device connect
proxy.write8(0x10005310, 0x02)

def fiforead(addr, length):
	data = ""
	for i in range(length):
		data += chr(proxy.read8(addr))
	return data

def fifowrite(addr, data):
	for c in data:
		proxy.write8(addr, ord(c))

def string_descriptor(s):
	utf = unicode(s).encode("utf-16le")
	fmt = "BB%ds"%len(utf)
	l = len(utf) + 2
	return (fmt, [l, 3, utf])

descriptors = {
	(1, 0): ("<BBHBBBBHHHBBBB",[ #DEVICE descriptor
		18, 1,				# length, descriptor type
		0x0101,				# USB version
		2, 0, 0,			# class, subclass, protocol
		64,					# max ep0 packet size
		0x1337, 0x1337,		# VID, PID
		0x0100,				# device version
		1, 2, 3,			# manufacturer, product, serial string IDs
		1,					# number of configurations
	]),
	(2, 0): (
		"<BBHBBBBB" + # CONFIGURATION descriptor
		"BBBBBBBBB" + # INTERFACE descriptor
		"BBBH" + # CDC descriptor
		"BBBBB" + # CDC CALL MANAGEMENT descriptor
		"BBBB" + # ACM FUNCTIONAL descriptor
		"BBBBB" + # ACM UNION descriptor
		"BBBBHB" + # ENDPOINT descriptor
		"BBBBBBBBB" + # INTERFACE descriptor
		"BBBBHB" + # ENDPOINT descriptor
		"BBBBHB", # ENDPOINT descriptor
		[
			# CONFIGURATION descriptor
			9, 2,			# length, descriptor type
			9+9+5+5+4+5+7+9+7+7,	# total length
			2,				# number of interfaces
			1,				# configuration value
			4,				# configuration name
			0xc0,			# attributes
			250,			# max power in units of 2mA
			
			# INTERFACE descriptor
			9, 4,			# length, descriptor type
			0, 0,			# interface number and alternate setting
			1,				# number of endpoints
			2, 2, 1,		# class, subclass, protocol = AT V.25TER (because we need to pick SOMETHING)
			5,				# interface name
			
			# CDC descriptor
			5, 0x24, 0x00,	# length, descriptor type, subtype
			0x0101,			# CDC version
			
			# CDC Call Management descriptor
			5, 0x24, 0x01,	# length, descriptor type, subtype
			0x00,			# capabilities
			0x01,			# data interface
			
			# ACM functional descriptor
			4, 0x24, 0x02,	# length, descriptor type, subtype
			0x00,			# capabilities
			
			# ACM union descriptor
			5, 0x24, 0x06,	# length, descriptor type, subtype
			0x00,			# master interface
			0x01,			# slave interface
			
			# ENDPOINT descriptor
			7, 5,			# length, descriptor type
			0x84,			# address
			0x03,			# attributes
			64,				# max packet size
			1,				# interval
			
			# INTERFACE descriptor
			9, 4,			# length, descriptor type
			1, 0,			# interface number and alternate setting
			2,				# number of endpoints
			10, 0, 0,		# class, subclass, protocol
			6,				# interface name
			
			# ENDPOINT descriptor
			7, 5,			# length, descriptor type
			0x82,			# address
			0x02,			# attributes
			64,				# max packet size
			1,				# interval
			
			# ENDPOINT descriptor
			7, 5,			# length, descriptor type
			0x03,			# address
			0x02,			# attributes
			64,				# max packet size
			1,				# interval
		]),
	(3, 0): ("<BBH",[ #STRING 0 (language info)
		4, 3, 0x409
	]),
	(3, 1): string_descriptor(u"Marcansoft"),
	(3, 2): string_descriptor(u"Marcan's h4x0r3d SPMP3052"),
	(3, 3): string_descriptor(u"00000000"),
	(3, 4): string_descriptor(u"CDC ACM serial port emulation"),
	(3, 5): string_descriptor(u"Control Interface"),
	(3, 6): string_descriptor(u"Data Interface"),
}

def put_ctl_data(data):
	print "put_ctl_data 0x%x"%len(data)
	fifowrite(0x10005000, data)
	proxy.clear8(0x100050c0, 4)
	proxy.set8(0x100050a0, 2)
	while not (proxy.read8(0x100050c0) & 4):
		pass
	print "ctl data sent"

def finish_control():
	proxy.clear8(0x100050c0, 4)
	proxy.set8(0x100050a0, 2)
	while not (proxy.read8(0x100050c0) & 4):
		pass
	
def get_ctl_data(l):
	proxy.clear8(0x100050c0, 2)
	proxy.set8(0x100050a0, 1)
	while not (proxy.read8(0x100050c0) & 2):
		pass
	return fiforead(0x10005000, l)

def usb_post_proc(data):
	proxy.write8(0x100050ec, 0)
	while not (proxy.read8(0x100050ec) & 0xc):
		pass
	v = proxy.read8(0x100050ec)
	queue_again = False
	if v & 8:
		print "flagged 1000003"
		if data is not None:
			put_ctl_data(data)
			queue_again = True
		# blah 1000003
	if v & 4:
		print "flagged 1000005"
		proxy.clear8(0x100050c0, 2)
		proxy.set8(0x100050a0, 1)
		while not (proxy.read8(0x100050c0) & 2):
			pass
		# blah 1000005
	if queue_again:
		print "Requeue"
		usb_post_proc(None)
		print "Requeue done"

def ctl_reply(data):
	while len(data):
		usb_post_proc(data[:0x40])
		data = data[0x40:]

def get_descriptor(wValue, wIndex, wLength):
	t = wValue >> 8
	i = wValue & 0xFF
	print "GET DESCRIPTOR %d %d %02x %d"%(t,i,wIndex,wLength)
	
	if (t,i) not in descriptors:
		print "======>Unhandled!"
	else:
		fmt, args = descriptors[(t,i)]
		data = struct.pack(fmt, *args)
		if len(data) > wLength:
			print "TOO LONG!"
		ctl_reply(data[:wLength])

def set_line_coding(wValue, wIndex, wLength):
	d=get_ctl_data(wLength)
	
	baud, stop, parity, bits = struct.unpack("<IBBB", d)
	
	stop = ['1','1.5','2'][stop]
	parity = "NOEMS"[parity]
	
	print "Parameters: %d %d%s%s"%(baud, bits, parity, stop)
	finish_control()

def set_control_line_state(wValue, wIndex, wLength):
	print "Control line state: 0x%04x"%wValue
	finish_control()

control_requests = {
	(0x80, 6): get_descriptor,
	(0x21, 0x20): set_line_coding,
	(0x21, 0x22): set_control_line_state,
}

def handle_control_request(req):
	bmRequestType, bRequest, wValue, wIndex, wLength = struct.unpack("<BBHHH", req)
	print "Control request %02x %02x %04x %04x %04x"%(bmRequestType, bRequest, wValue, wIndex, wLength)
	
	if (bmRequestType, bRequest) not in control_requests:
		print "======>Unhandled!"
	else:
		control_requests[(bmRequestType, bRequest)](wValue, wIndex, wLength)
	

while True:
	while not (proxy.read8(0x100050c0) & 1):
		proxy.read8(0x100050c2) #??
	print "IRQ signalled"
	proxy.clear8(0x100050c0, 1)
	
	ctl = fiforead(0x10005000, 8)
	
	handle_control_request(ctl)
