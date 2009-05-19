#!/usr/bin/python

from __main__ import *

# ARM utilities

#these silly classes are just used to "typecheck" register/copro arguments
class Reg:
	def __init__(self, rn):
		self.rn = rn

class CReg:
	def __init__(self, crn):
		self.crn = crn

class CPro:
	def __init__(self, cpr):
		self.cpr = cpr

r0 = Reg(0)
r1 = Reg(1)
r2 = Reg(2)
r3 = Reg(3)
r4 = Reg(4)
r5 = Reg(5)
r6 = Reg(6)
r7 = Reg(7)
r8 = Reg(8)
r9 = Reg(9)
r10 = Reg(10)
r11 = Reg(11)
r12 = Reg(12)
r13 = Reg(13)
r14 = Reg(14)
r15 = Reg(15)

sp = r13
lr = r14
pc = r15

c0 = CReg(0)
c1 = CReg(1)
c2 = CReg(2)
c3 = CReg(3)
c4 = CReg(4)
c5 = CReg(5)
c6 = CReg(6)
c7 = CReg(7)
c8 = CReg(8)
c9 = CReg(9)
c10 = CReg(10)
c11 = CReg(11)
c12 = CReg(12)
c13 = CReg(13)
c14 = CReg(14)
c15 = CReg(15)

p0 = CPro(0)
p1 = CPro(1)
p2 = CPro(2)
p3 = CPro(3)
p4 = CPro(4)
p5 = CPro(5)
p6 = CPro(6)
p7 = CPro(7)
p8 = CPro(8)
p9 = CPro(9)
p10 = CPro(10)
p11 = CPro(11)
p12 = CPro(12)
p13 = CPro(13)
p14 = CPro(14)
p15 = CPro(15)

SCRATCH=0x24F00000
BXLR=0xE12FFF1E

def make_mcr(copro, op1, rd, crn, crm, op2=0):
	assert 0 <= op1 <= 7
	assert 0 <= op2 <= 7
	i = 0xEE000010
	i |= op1<<21
	i |= crn.crn<<16
	i |= rd.rn<<12
	i |= copro.cpr<<8
	i |= op2<<5
	i |= crm.crn<<0
	return i

def make_mrc(copro, op1, rd, crn, crm, op2=0):
	return make_mcr(copro, op1, rd, crn, crm, op2) | 0x00100000

def mrc(copro, op1, crn, crm, op2=2):
	global write32, call
	i = make_mrc(copro, op1, r0, crn, crm, op2)
	write32(SCRATCH, i)
	write32(SCRATCH+4, BXLR)
	return call(SCRATCH)

def mcr(copro, op1, value, crn, crm, op2=0):
	global write32, call
	i = make_mcr(copro, op1, r0, crn, crm, op2)
	write32(SCRATCH, i)
	write32(SCRATCH+4, BXLR)
	call(SCRATCH, value)

