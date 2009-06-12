#!/usr/bin/python

from numpy import *
from math import *

class Model:
	def __init__(self, plyfile=None):
		self.vertices = []
		self.faces = []
		self.lines = None
		if plyfile is not None:
			self.read(plyfile)
	def read(self, file):
		fd = open(file)
		if fd.readline() != "ply\n":
			raise Exception("not a ply file")
		vlist = []
		if fd.readline() != "format ascii 1.0\n":
			raise Exception("unknown ply format")
		nv = None
		nf = None
		while True:
			l = fd.readline()[:-1]
			v = l.split()
			if v[0] == "comment":
				continue
			elif v[0] == "element":
				if v[1] == "vertex":
					nv = int(v[2])
				elif v[1] == "face":
					nf = int(v[2])
			elif v[0] == "end_header":
				break
		for i in range(nv):
			vertex = tuple(map(float, fd.readline()[:-1].split()))
			if vertex in self.vertices:
				vlist.append(self.vertices.index(vertex))
			else:
				vlist.append(len(self.vertices))
				self.vertices.append(vertex)
		for i in range(nf):
			face = map(int, fd.readline()[:-1].split())
			if face[0] != 3:
				raise Exception("Face with %d vertices not supported"%len(face))
			a,b,c = face[1:]
			self.faces.append((vlist[a], vlist[b], vlist[c]))
	def getlines(self):
		if self.lines is not None:
			return self.lines
		# get all unique lines
		nl = set()
		for a,b,c in self.faces:
			if (b,a) not in nl:
				nl.add((a,b))
			if (a,c) not in nl:
				nl.add((a,c))
			if (c,b) not in nl:
				nl.add((b,c))
		# calculate vertex use count per line
		vuse = [0] * len(self.vertices)
		for a,b in nl:
			vuse[a] += 1
			vuse[b] += 1
		self.lines = []
		while nl:
			mi = -1
			mx = 0
			# find the most used vertex
			for i,x in enumerate(vuse):
				if x > mx:
					mx = x
					mi = i
			# find all lines containing it
			nl2 = set()
			for a,b in nl:
				if a == mi:
					self.lines.append((a,b))
					vuse[a] -= 1
					vuse[b] -= 1
				elif b == mi:
					self.lines.append((b,a))
					vuse[a] -= 1
					vuse[b] -= 1
				else:
					nl2.add((a,b))
			nl = nl2
			assert vuse[mi] == 0
		return self.lines

bunny = Model("bunny.ply")
print "/* %d vertices */"%len(bunny.vertices)
print "/* %d faces */"%len(bunny.faces)
print "/* %d lines */"%len(bunny.getlines())

s = 30

rx = 0
ry = 0
rz = 0

pzv = 1000.0

def transform(v,rmat):
	x,y,z = v[0]*s,v[1]*s,-v[2]*s
	y -= 0.8 * s
	x,y,z = dot((x,y,z),rmat)
	z += pzv
	pf = pzv / z
	#pf = pf
	x *= pf
	y *= pf
	x += 160
	y += 120
	return (x,y)

def wireRender(model, rot):
	lines = []
	tv = []
	for v in model.vertices:
		tv.append(transform(v,rot))
	for a,b in model.getlines():
		lines.append((tv[a],tv[b]))
	return lines

def xrot(a):
	return array([
		[1,0,0],
		[0,cos(a),-sin(a)],
		[0,sin(a),cos(a)]
	])

def yrot(a):
	return array([
		[cos(a),0,sin(a)],
		[0,1,0],
		[-sin(a),0,cos(a)]
	])

def gen(rx, ry, rz):
	rmat = identity(3, float)
	rmat = dot(rmat, xrot(rx))
	rmat = dot(rmat, yrot(ry))
	rmat = dot(rmat, yrot(rz))
	return wireRender(bunny, rmat)

if __name__ == "__main__":
	bunny.getlines()
	print '#include "types.h"'
	print
	print '#define BUNNY_VERTEX_COUNT %d'%len(bunny.vertices)
	print '#define BUNNY_LINE_COUNT %d'%len(bunny.lines)
	print
	print 'const s32 bunny_v[%d][3] = {'%len(bunny.vertices)
	for v in bunny.vertices:
		x,y,z = v[0]*s,v[1]*s,-v[2]*s
		y -= 0.8 * s
		x,y,z = [" -"[c<0] + "0x%05x"%abs(int(c * 65536)) for c in (x,y,z)]
		print "\t{%11s, %11s, %11s},"%(x,y,z)
	print '};'
	print 'const u16 bunny_l[%d][2] = {'%len(bunny.lines)
	for i,(s,e) in enumerate(bunny.lines):
		if i%8 == 0:
			print "\t{%4d, %4d},"%(s,e),
		elif i%8 == 7:
			print "{%4d, %4d},"%(s,e)
		else:
			print "{%4d, %4d},"%(s,e),
	print
	print '};'
