/*
	mini - minimp - port of MINI to the spmp305x

Copyright (C) 2008, 2009	Hector Martin "marcan" <marcan@marcansoft.com>

# This code is licensed to you under the terms of the GNU GPL, version 2;
# see file COPYING or http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
*/

#include "types.h"
#include "utils.h"
#include "start.h"
#include "spmp3050.h"
#include "string.h"
#include "memory.h"
#include "uart.h"
#include "panic.h"
#include "irq.h"
#include "exception.h"
#include "uartproxy.h"

u32 _main(void)
{
	uart_init();
	debug_printf("minimp v0.1 loading\n");

	debug_printf("Initializing exceptions...\n");
	exception_initialize();
	//debug_printf("Configuring caches and MMU...\n");
	//mem_initialize();

	//irq_initialize();
	//debug_printf("Interrupts initialized\n");
	
	uartproxy_run();
	
	while(1)
		debug_printf("UART: got '%c'\n", uart_getchar());

	//debug_printf("Shutting down interrupts...\n");
	//irq_shutdown();
	//debug_printf("Shutting down caches and MMU...\n");
	//mem_shutdown();
	
	while(1);

	return 0;
}

