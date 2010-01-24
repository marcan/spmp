#!/usr/bin/python

import serial, os, struct, time, struct, array
from proxy import *
import initlib

import spmp305x as spmp

iface = spmp.iface
proxy = spmp.proxy
regs = spmp.regs

print "Power on enable"

proxy.set32(0x1000b064, 2)
proxy.set32(0x1000b068, 2)
proxy.clear32(0x1000b320, 2)
