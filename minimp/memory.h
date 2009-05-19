/*
	mini - a Free Software replacement for the Nintendo/BroadOn IOS.
	memory management, MMU, caches, and flushing

Copyright (C) 2008, 2009	Hector Martin "marcan" <marcan@marcansoft.com>

# This code is licensed to you under the terms of the GNU GPL, version 2;
# see file COPYING or http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
*/

#ifndef __MEMORY_H__
#define __MEMORY_H__

#include "types.h"

#define ALIGN_FORWARD(x,align) \
	((typeof(x))((((u32)(x)) + (align) - 1) & (~(align-1))))

#define ALIGN_BACKWARD(x,align) \
	((typeof(x))(((u32)(x)) & (~(align-1))))

void dc_flushrange(const void *start, u32 size);
void dc_invalidaterange(void *start, u32 size);
void dc_flushall(void);
void ic_invalidateall(void);

void mem_initialize(void);
void mem_shutdown(void);

u32 dma_addr(void *);

static inline u32 get_cr(void)
{
	u32 data;
	__asm__ volatile ( "mrc\tp15, 0, %0, c1, c0, 0" : "=r" (data) );
	return data;
}

static inline u32 get_ttbr(void)
{
	u32 data;
	__asm__ volatile ( "mrc\tp15, 0, %0, c2, c0, 0" : "=r" (data) );
	return data;
}

static inline u32 get_dacr(void)
{
	u32 data;
	__asm__ volatile ( "mrc\tp15, 0, %0, c3, c0, 0" : "=r" (data) );
	return data;
}

static inline void set_cr(u32 data)
{
	__asm__ volatile ( "mcr\tp15, 0, %0, c1, c0, 0" :: "r" (data) );
}

static inline void set_ttbr(u32 data)
{
	__asm__ volatile ( "mcr\tp15, 0, %0, c2, c0, 0" :: "r" (data) );
}

static inline void set_dacr(u32 data)
{
	__asm__ volatile ( "mcr\tp15, 0, %0, c3, c0, 0" :: "r" (data) );
}

static inline u32 get_dfsr(void)
{
	u32 data;
	__asm__ volatile ( "mrc\tp15, 0, %0, c5, c0, 0" : "=r" (data) );
	return data;
}

static inline u32 get_ifsr(void)
{
	u32 data;
	__asm__ volatile ( "mrc\tp15, 0, %0, c5, c0, 1" : "=r" (data) );
	return data;
}

static inline u32 get_far(void)
{
	u32 data;
	__asm__ volatile ( "mrc\tp15, 0, %0, c6, c0, 0" : "=r" (data) );
	return data;
}

#endif

