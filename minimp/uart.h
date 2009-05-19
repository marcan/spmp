/*
	minimp - port of MINI to the SPP305x
	uart

Copyright (C) 2008, 2009	Hector Martin "marcan" <marcan@marcansoft.com>

# This code is licensed to you under the terms of the GNU GPL, version 2;
# see file COPYING or http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
*/

#ifndef __UART_H__
#define __UART_H__

#include "types.h"

void uart_init(void);

char uart_getchar(void);

u32 uart_recvbuffer_safe(void *buf, u32 len);
u32 uart_sendbuffer_safe(void *buf, u32 len);

int uart_puts(const char *buf);

#ifdef NDEBUG
#define debug_printf(...) do { } while(0)
#else
int debug_printf(const char *fmt, ...) __attribute__((format (printf, 1, 2)));
#endif

#endif

