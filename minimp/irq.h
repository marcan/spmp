/*
	mini - a Free Software replacement for the Nintendo/BroadOn IOS.
	IRQ support

Copyright (C) 2008, 2009	Hector Martin "marcan" <marcan@marcansoft.com>
Copyright (C) 2008, 2009	Sven Peter <svenpeter@gmail.com>

# This code is licensed to you under the terms of the GNU GPL, version 2;
# see file COPYING or http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
*/

#ifndef __IRQ_H__
#define __IRQ_H__

#define CPSR_IRQDIS 0x80
#define CPSR_FIQDIS 0x40

#include "types.h"

#define IRQ_ALARM_MS2REG(x)	(1898 * x)

void irq_initialize(void);
void irq_shutdown(void);

void irq_enable(u32 irq);
void irq_disable(u32 irq);

u32 irq_kill(void);
void irq_restore(u32 cookie);

static inline void irq_wait(void)
{
	u32 data = 0;
	__asm__ volatile ( "mcr\tp15, 0, %0, c7, c0, 4" : : "r" (data) );
}

void irq_set_alarm(u32 ms, u8 enable);

#endif

