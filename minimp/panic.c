/*
	mini - a Free Software replacement for the Nintendo/BroadOn IOS.
	panic flash codes

Copyright (C) 2008, 2009	Hector Martin "marcan" <marcan@marcansoft.com>

# This code is licensed to you under the terms of the GNU GPL, version 2;
# see file COPYING or http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
*/

#include "types.h"
#include "utils.h"
#include "start.h"
#include "spmp3050.h"
#include <stdarg.h>

#define PANIC_ON	200000
#define PANIC_OFF	300000
#define PANIC_INTER	1000000

//TODO
void panic2(int mode, ...)
{
	int arg;
	va_list ap;

	while(1) {
		va_start(ap, mode);
		
		while(1) {
			arg = va_arg(ap, int);
			if(arg < 0)
				break;
			udelay(arg * PANIC_ON);
			udelay(PANIC_OFF);
		}
		
		va_end(ap);
		
		udelay(PANIC_INTER);
	}
}

