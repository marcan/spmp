#!/usr/bin/python

class Function(object):
	def __init__(self):
		pass
	def to_c(self):
		return self.to_python() + ";"

class BuiltinFunction(Function):
	pass

class delay_base(BuiltinFunction):
	def __init__(self, time):
		self.time=time
	def to_python(self):
		return "delay(%d)"%self.time

class delay_x160(delay_base):
	def __init__(self, time):
		self.time = time*160

class delay_master(delay_base):
	pass #TODO:???

class LCD_WriteReg(BuiltinFunction):
	def __init__(self, reg, value):
		assert 0 <= value <= 0xFFFF
		assert 0 <= reg <= 0xFF
		self.reg = reg
		self.value = value
	def to_python(self):
		return "LCD_WriteReg(0x%02x, 0x%x)"%(self.reg, self.value)

class LCD_SetRegAddr(BuiltinFunction):
	def __init__(self, reg):
		assert 0 <= reg <= 0xFF
		self.reg = reg
	def to_python(self):
		return "LCD_SetRegAddr(0x%02x)"%(self.reg)

class LCD_WriteRegData(BuiltinFunction):
	def __init__(self, value):
		assert 0 <= value <= 0xFFFF
		self.value = value
	def to_python(self):
		return "LCD_WriteRegData(0x%x)"%(self.value)

class InitFunction(Function):
	def __init__(self, name, contents):
		self.name = name
		while contents and isinstance(contents[0],delay_base):
			contents = contents[1:]
		for i in range(len(contents)-1):
			if i >= (len(contents)-2):
				break
			if isinstance(contents[i],LCD_SetRegAddr) and isinstance(contents[i+1],LCD_WriteRegData):
				reg = contents[i].reg
				value = contents[i+1].value
				contents = contents[:i] + [LCD_WriteReg(reg,value)] + contents[i+2:]
		self.contents = contents
	def body_python(self):
		s = "def %s():\n"%self.name
		for f in self.contents:
			s += "\t" + f.to_python() + "\n"
		s += "\n"
		return s
	def body_c(self):
		s = "void %s(void)\n{\n"%self.name
		for f in self.contents:
			s += "\t" + f.to_c() + "\n"
		s += "}\n"
		return s
	def to_python(self):
		return "%s()"%(self.name)
