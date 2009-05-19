/*
	mini - a Free Software replacement for the Nintendo/BroadOn IOS.
	IRQ support

Copyright (C) 2008, 2009	Hector Martin "marcan" <marcan@marcansoft.com>
Copyright (C) 2008, 2009	Sven Peter <svenpeter@gmail.com>
Copyright (C) 2009		Andre Heider "dhewg" <dhewg@wiibrew.org>

# This code is licensed to you under the terms of the GNU GPL, version 2;
# see file COPYING or http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
*/

#include "irq.h"
#include "spmp3050.h"
#include "uart.h"
#include "utils.h"

void irq_setup_stack(void);

void irq_initialize(void)
{
	irq_setup_stack();
	irq_restore(CPSR_FIQDIS);

}

void irq_shutdown(void)
{
	irq_kill();
}

void irq_handler(void)
{
	debug_printf("IRQ!\n");
	while(1);
}

void irq_enable(u32 irq)
{
}

void irq_disable(u32 irq)
{
}


