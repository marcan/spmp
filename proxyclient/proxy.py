#!/usr/bin/python

import os, sys, struct

def hexdump(s,sep=" "):
	return sep.join(map(lambda x: "%02x"%ord(x),s))

def ascii(s):
	s2 = ""
	for c in s:
		if ord(c)<0x20 or ord(c)>0x7e:
			s2 += "."
		else:
			s2 += c
	return s2

def pad(s,c,l):
	if len(s)<l:
		s += c * (l-len(s))
	return s

def chexdump(s,st=0):
	for i in range(0,len(s),16):
		print "%08x  %s  %s  |%s|"%(i+st,pad(hexdump(s[i:i+8],' ')," ",23),pad(hexdump(s[i+8:i+16],' ')," ",23),pad(ascii(s[i:i+16])," ",16))


class UartError(RuntimeError):
	pass

class UartTimeout(UartError):
	pass

class UartCMDError(UartError):
	pass

class UartCRCError(UartError):
	pass

class UartRemoteError(UartError):
	pass

class UartInterface:
	REQ_NOP = 0x00AA55FF
	REQ_PROXY = 0x01AA55FF
	REQ_MEMREAD = 0x02AA55FF
	REQ_MEMWRITE = 0x03AA55FF
	ST_OK = 0
	ST_BADCMD = -1
	ST_INVAL = -2
	ST_XFERERR = -3
	ST_CRCERR = -4

	def __init__(self, device, debug=False):
		self.debug = debug
		self.dev = device
		self.dev.timeout = 0
		self.dev.flushOutput()
		self.dev.flushInput()
		d = self.dev.read(1)
		while d != "":
			d = self.dev.read(1)
		self.dev.timeout = 1.0

	def checksum(self, data):
		sum = 0xDEADBEEF;
		for c in data:
			sum *= 31337
			sum += ord(c) ^ 0x5a
			sum &= 0xFFFFFFFF

		return (sum ^ 0xADDEDBAD) & 0xFFFFFFFF

	def readfull(self, size):
		d = self.dev.read(size)
		if len(d) != size:
			raise UartTimeout("Expected %d bytes, got %d bytes"%(size,len(d)))
		return d

	def cmd(self, cmd, payload):
		if len(payload) > 28:
			raise ValueError("Incorrect payload size %d"%len(payload))

		payload = payload + "\x00" * (28 - len(payload))
		command = struct.pack("<I", cmd) + payload
		command += struct.pack("<I", self.checksum(command))
		if self.debug:
			print "<<", hexdump(command)
		self.dev.write(command)

	def reply(self, cmd):
		while True:
			reply = self.readfull(1)
			if reply != "\xff":
				if self.debug:
					print ">>", hexdump(reply[-1]), repr(reply[-1])
				continue
			reply += self.readfull(1)
			if reply != "\xff\x55":
				if self.debug:
					print ">>", hexdump(reply[-1])
				continue
			reply += self.readfull(1)
			if reply != "\xff\x55\xaa":
				if self.debug:
					print ">>", hexdump(reply[-1])
				continue
			reply += self.readfull(21)
			if self.debug:
				print ">>", hexdump(reply)
			cmdin, status, data, checksum = struct.unpack("<Ii12sI", reply)
			ccsum = self.checksum(reply[:-4])
			if checksum != ccsum:
#				raise UartCRCError("Reply checksum error: Expected 0x%08x, got 0x%08x"%(checksum, ccsum))
				print "Reply checksum error: Expected 0x%08x, got 0x%08x"%(checksum, ccsum)

			if cmdin != cmd:
				raise UartCMDError("Reply command mismatch: Expected 0x%08x, got 0x%08x"%(cmd, cmdin))
			if status != self.ST_OK:
				if status == self.ST_BADCMD:
					raise UartRemoteError("Reply error: Bad Command")
				elif status == self.ST_INVAL:
					raise UartRemoteError("Reply error: Invalid argument")
				elif status == self.ST_XFERERR:
					raise UartRemoteError("Reply error: Data transfer failed")
				elif status == self.ST_CRCERR:
					raise UartRemoteError("Reply error: Data checksum failed")
				else:
					raise UartRemoteError("Reply error: Unknown error (%d)"%status)
			return data

	def nop(self):
		self.cmd(self.REQ_NOP, "")
		self.reply(self.REQ_NOP)

	def proxyreq(self, req):
		self.cmd(self.REQ_PROXY, req)
		return self.reply(self.REQ_PROXY)

	def writemem(self, addr, data):
		checksum = self.checksum(data)
		size = len(data)
		req = struct.pack("<III", addr, size, checksum)
		self.cmd(self.REQ_MEMWRITE, req)
		if self.debug:
			print "<< DATA:"
			chexdump(data)
		self.dev.write(data)
		# should automatically report a CRC failure
		self.reply(self.REQ_MEMWRITE)

	def readmem(self, addr, size):
		req = struct.pack("<II", addr, size)
		self.cmd(self.REQ_MEMREAD, req)
		reply = self.reply(self.REQ_MEMREAD)
		checksum = struct.unpack("<I",reply[:4])[0]
		data = self.readfull(size)
		if self.debug:
			print ">> DATA:"
			chexdump(data)
		ccsum = self.checksum(data)
		if checksum != ccsum:
#			raise UartCRCError("Reply data checksum error: Expected 0x%08x, got 0x%08x"%(checksum, ccsum))
			print "Reply data checksum error: Expected 0x%08x, got 0x%08x"%(checksum, ccsum)
		return data

class ProxyError(RuntimeError):
	pass

class ProxyCMDError(ProxyError):
	pass

class ProxyRemoteError(ProxyError):
	pass

class AlignmentError(Exception):
	pass

class SPMPProxy:
	S_OK = 0
	S_BADCMD = -1

	P_NOP = 0x000
	P_EXIT = 0x001
	P_CALL = 0x002

	P_WRITE32 = 0x100
	P_WRITE16 = 0x101
	P_WRITE8 = 0x102
	P_READ32 = 0x103
	P_READ16 = 0x104
	P_READ8 = 0x105
	P_SET32 = 0x106
	P_SET16 = 0x107
	P_SET8 = 0x108
	P_CLEAR32 = 0x109
	P_CLEAR16 = 0x10a
	P_CLEAR8 = 0x10b
	P_MASK32 = 0x10c
	P_MASK16 = 0x10d
	P_MASK8 = 0x10e

	P_MEMCPY32 = 0x200
	P_MEMCPY16 = 0x201
	P_MEMCPY8 = 0x202
	P_MEMSET32 = 0x203
	P_MEMSET16 = 0x204
	P_MEMSET8 = 0x205

	P_DC_FLUSHRANGE = 0x300
	P_DC_INVALRANGE = 0x301
	P_DC_FLUSHALL = 0x302
	P_IC_INVALALL = 0x303
	P_MAGIC_BULLSHIT = 0x304
	P_AHB_MEMFLUSH = 0x305
	P_MEM_PROTECT = 0x306

	P_NAND_READPAGE = 0x400
	P_NAND_WRITEPAGE = 0x401
	P_NAND_ERASEBLOCK = 0x402
	P_NAND_GETSTATUS = 0x403

	def __init__(self, iface, debug=False):
		self.debug = debug
		self.iface = iface

	def request(self, opcode, *args):
		if len(args) > 6:
			raise ValueError("Too many arguments")
		args = list(args) + [0] * (6 - len(args))
		req = struct.pack("<IIIIIII", opcode, *args)
		if self.debug:
			print "<<<< %08x: %08x %08x %08x %08x %08x %08x"%tuple([opcode] + args)
		reply = self.iface.proxyreq(req)
		rop, status, retval = struct.unpack("<IiI", reply)
		if self.debug:
			print ">>>> %08x: %d %08x"%(rop, status, retval)
		if rop != opcode:
			raise ProxyCMDError("Reply opcode mismatch: Expected 0x%08x, got 0x%08x"%(opcode,rop))
		if status != self.S_OK:
			if status == self.S_BADCMD:
				raise ProxyRemoteError("Reply error: Bad Command")
			else:
				raise ProxyRemoteError("Reply error: Unknown error (%d)"%status)
		return retval

	def nop(self):
		self.request(self.P_NOP)
	def exit(self):
		self.request(self.P_EXIT)
	def call(self, addr, *args):
		if len(args) > 4:
			raise ValueError("Too many arguments")
		return self.request(self.P_CALL, addr, *args)

	def write32(self, addr, data):
		if addr & 3:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_WRITE32, addr, data)
	def write16(self, addr, data):
		if addr & 1:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_WRITE16, addr, data)
	def write8(self, addr, data):
		self.request(self.P_WRITE8, addr, data)

	def read32(self, addr):
		if addr & 3:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		return self.request(self.P_READ32, addr)
	def read16(self, addr):
		if addr & 1:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		return self.request(self.P_READ16, addr)
	def read8(self, addr):
		return self.request(self.P_READ8, addr)

	def set32(self, addr, data):
		if addr & 3:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_SET32, addr, data)
	def set16(self, addr, data):
		if addr & 1:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_SET16, addr, data)
	def set8(self, addr, data):
		self.request(self.P_SET8, addr, data)

	def clear32(self, addr, data):
		if addr & 3:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_CLEAR32, addr, data)
	def clear16(self, addr, data):
		if addr & 1:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_CLEAR16, addr, data)
	def clear8(self, addr, data):
		self.request(self.P_CLEAR8, addr, data)

	def mask32(self, addr, clear, set):
		if addr & 3:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_CLEAR32, clear, set)
	def mask16(self, addr, clear, set):
		if addr & 1:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_CLEAR16, clear, set)
	def mask8(self, addr, clear, set):
		self.request(self.P_CLEAR8, clear, set)

	def memcpy32(self, dst, src, size):
		if src & 3 or dst & 3:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_MEMCPY32, dst, src, size)
	def memcpy16(self, dst, src, size):
		if src & 1 or dst & 1:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_MEMCPY16, dst, src, size)
	def memcpy8(self, dst, src, size):
		self.request(self.P_MEMCPY8, dst, src, size)

	def memset32(self, dst, src, size):
		if dst & 3:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_MEMSET32, dst, src, size)
	def memset16(self, dst, src, size):
		if dst & 1:
			raise AlignmentError("Unaligned access. You were going to crash SPMP, but I'll be nice and spare you the reboot.")
		self.request(self.P_MEMSET16, dst, src, size)
	def memset8(self, dst, src, size):
		self.request(self.P_MEMSET8, dst, src, size)
	
	def dc_flushrange(self, addr, size):
		self.request(self.P_DC_FLUSHRANGE, addr, size)
	def dc_invalrange(self, addr, size):
		self.request(self.P_DC_INVALRANGE, addr, size)
	def dc_flushall(self):
		self.request(self.P_DC_FLUSHALL)
	def ic_invalall(self):
		self.request(self.P_IC_INVALALL)
	def magic_bullshit(self, n):
		self.request(self.P_MAGIC_BULLSHIT, n)
	def ahb_memflush(self, n):
		self.request(self.P_AHB_MEMFLUSH, n)
	def mem_protect(self, start, end):
		self.request(self.P_MEM_PROTECT, start, end)

	def nand_readpage(self, page, data_addr, ecc_addr):
		self.request(self.P_NAND_READPAGE, page, data_addr, ecc_addr)
	def nand_writepage(self, page, data_addr, ecc_addr):
		self.request(self.P_NAND_WRITEPAGE, page, data_addr, ecc_addr)
	def nand_eraseblock(self, block):
		self.request(self.P_NAND_ERASEBLOCK, block)
	def nand_getstatus(self):
		return self.request(self.P_NAND_GETSTATUS)

if __name__ == "__main__":
	import serial
	uartdev = os.environ.get("SPMPDEVICE", "/dev/ttyUSB0")
	usbuart = serial.Serial(uartdev, 115200)
	uartif = UartInterface(usbuart, debug=True)
	print "Sending NOP...",
	uartif.nop()
	print "OK"
	proxy = SPMPProxy(uartif)
	print "Sending Proxy NOP...",
	proxy.nop()
	print "OK"


