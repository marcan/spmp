#!/usr/bin/python
import sys, os, re

class EmuRunner(object):
	
	ARGCOUNTS={
		'delay_base':1,
		'delay_x160':1,
		'or_a00f':-1,
		'set_fb_size_params':-4,
		'more_gfx_magic':-1,
		'LCD_WriteReg':2,
		'LCD_SetRegAddr':1,
		'LCD_WriteRegData':1,
		'set_a000_enable_lcd_maybe':-1,
		'set_a203_bit0_inv':-1,
	}
	
	def __init__(self, of):
		self.of = of
		self.indent = 0
	
	def out(self, text=""):
		print >>self.of, "\t" * self.indent + text
	
	def rn(self, x):
		assert x != "PC"
		if x == "SP":
			return 13
		if x == "LR":
			return 14
		assert x[0] == 'R',x
		return int(x[1:])
	
	def astr(self, x, fn):
		if isinstance(x,str):
			return x
		elif isinstance(x,int) or isinstance(x,long):
			if x < 10 or 'delay' in fn:
				return str(x)
			else:
				return hex(x)
		elif x is None:
			return "None"
		else:
			assert False
	
	def regornum(self, s):
		assert s != "PC"
		if s[0] == 'R' or s in ["SP", "LR"]:
			return self.regs[self.rn(s)]
		elif s[0] == '#':
			return int(s[1:],0)
		else:
			return int(s,0)
	
	def run(self, name, lines):
		self.regs = [None] * 16
		self.out("%s = InitFunction('%s', ["%(name,name))
		self.indent+=1
		dead = False
		for l in lines:
			self.out("# %s"%l)
			if dead:
				continue
			if '-------------------' in l:
				dead = True
				continue
			if ';' in l:
				l = l.split(";",1)[0]
			if l[0] != " ":
				lname = l.split()[0]
				self.out("## label %s"%lname)
			else:
				l = l.strip()
				if not l:
					continue
				ins, args = l.split(None, 1)
				args = args.replace(" ","")
				args = args.split(",")
				if ins in ['B','BL']:
					fname = args[0]
					dis = False
					if fname in self.ARGCOUNTS:
						ac = self.ARGCOUNTS[fname]
						if ac<0:
							dis = True
							ac = -ac
						assert ac <= 4
						fargs = [self.astr(x, fname) for x in self.regs[:ac]]
					else:
						dis = True
						fargs = ["UNKNOWN"]
					if dis:
						self.out("##%s(%s),"%(fname,','.join(fargs)))
					else:
						self.out("%s(%s),"%(fname,','.join(fargs)))
					self.regs[0] = self.regs[1] = self.regs[2] = self.regs[3] = None
					if ins == 'B':
						dead = True
				elif ins == 'MOV':
					dreg = self.rn(args[0])
					self.regs[dreg] = self.regornum(args[1])
				elif ins in ['ADD','SUB','RSB','ORR','AND','BIC']:
					assert len(args) == 3
					dreg = self.rn(args[0])
					areg = self.rn(args[1])
					if self.regs[areg] is None or self.regornum(args[2]) is None:
						self.regs[dreg] = None
					else:
						if ins == 'ADD':
							self.regs[dreg] = self.regs[areg] +  self.regornum(args[2])
						elif ins == 'SUB':
							self.regs[dreg] = self.regs[areg] -  self.regornum(args[2])
						elif ins == 'RSB':
							self.regs[dreg] = self.regornum(args[2]) - self.regs[areg]
						elif ins == 'ORR':
							self.regs[dreg] = self.regs[areg] | self.regornum(args[2])
						elif ins == 'AND':
							self.regs[dreg] = self.regs[areg] & self.regornum(args[2])
						elif ins == 'BIC':
							self.regs[dreg] = self.regs[areg] & (self.regornum(args[2]) ^ 0xFFFFFFFF)
				elif ins in ['LDRB', 'LDR', 'LDRH']:
					self.regs[self.rn(args[0])] = None
			self.regs = [x and x & 0xFFFFFFFF for x in self.regs]
		self.indent-=1
		self.out("])")
		self.out()

f = open(sys.argv[1])

subs = []

in_sub = False
have_name = False

print "Reading subroutines from input..."

of = open(sys.argv[2], "w")

print >>of, "from classes import *"

for line in f:
	while line and line[-1] in "\r\n":
		line = line[:-1]
	if not line:
		continue
	line = line.split(":",1)[1]
	if ' ' not in line:
		continue
	line = line.split(" ",1)[1]
	if not line:
		continue
	if not in_sub:
		if "S U B R O U T I N E" in line:
			in_sub = True
		continue
	if in_sub:
		if not have_name:
			if line[0] != " ":
				name = line.split()[0]
				sublines = []
				have_name = 1
				continue
		else:
			if "End of function" in line:
				subs.append((name, sublines))
				in_sub = have_name = False
			else:
				sublines.append(line)

print "Found %d subroutines"%len(subs)

er = EmuRunner(of)

for name, lines in subs:
	print "Processing subroutine " + name
	er.run(name, lines)

print "All done"
of.close()

