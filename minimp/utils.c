/*
	mini - a Free Software replacement for the Nintendo/BroadOn IOS.
	random utilities

Copyright (C) 2008, 2009	Hector Martin "marcan" <marcan@marcansoft.com>

# This code is licensed to you under the terms of the GNU GPL, version 2;
# see file COPYING or http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
*/

#include "types.h"
#include "utils.h"
#include "uart.h"
#include "vsprintf.h"
#include "start.h"
#include "spmp3050.h"

static char ascii(char s) {
  if(s < 0x20) return '.';
  if(s > 0x7E) return '.';
  return s;
}

void hexdump(void *d, int len) {
  u8 *data;
  int i, off;
  data = (u8*)d;
  for (off=0; off<len; off += 16) {
    debug_printf("%08x  ",off);
    for(i=0; i<16; i++)
      if((i+off)>=len) debug_printf("   ");
      else debug_printf("%02x ",data[off+i]);

    debug_printf(" ");
    for(i=0; i<16; i++)
      if((i+off)>=len) debug_printf(" ");
      else debug_printf("%c",ascii(data[off+i]));
    debug_printf("\n");
  }
}

void udelay(u32 d)
{
	// TODO
}

void panic(u8 v)
{
	while(1) {
		//TODO
		udelay(500000);
		udelay(500000);
	}
}

