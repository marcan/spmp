/*
	mini - a Free Software replacement for the Nintendo/BroadOn IOS.
	linker script
	
Copyright (C) 2008, 2009	Hector Martin "marcan" <marcan@marcansoft.com>

# This code is licensed to you under the terms of the GNU GPL, version 2;
# see file COPYING or http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
*/

OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
EXTERN(_start)
EXTERN(__ipc_info)
ENTRY(_start)

__stack_size = 0x1000;
__irqstack_size = 0x200;
__excstack_size = 0x200;

MEMORY {
	sdram		: ORIGIN = 0x24000000, LENGTH = 16M
}

SECTIONS
{
	.init :
	{
		*(.init)
		. = ALIGN(64);
	} >sdram

	.text :
	{
		*(.text*)
		*(.text.*)
		*(.gnu.warning)
		*(.gnu.linkonce.t*)
		*(.glue_7)
		*(.glue_7t)
		. = ALIGN(64);
	} >sdram

	.rodata :
	{
		*(.rodata)
		*all.rodata*(*)
		*(.roda)
		*(.rodata.*)
		*(.gnu.linkonce.r*)
		. = ALIGN(64);
	} >sdram

	.data :
	{
		*(.data)
		*(.data.*)
		*(.gnu.linkonce.d*)
		. = ALIGN(64);
	} >sdram

	.sploadfailsprobablyduetolibusb :
	{
		LONG(0xdefeca7e);
	} > sdram

	.bss :
	{
		__bss_start = . ;
		*(.dynbss)
		*(.gnu.linkonce.b*)
		*(.bss*)
		*(COMMON)
		. = ALIGN(64);
		__bss_end = . ;
	} >sdram

	.stack :
	{
		. = ALIGN(16);
		__stack_end = .;
		. = . +__stack_size;
		. = ALIGN(16);
		__stack_addr = .;
		__irqstack_end = .;
		. = . +__irqstack_size;
		. = ALIGN(16);
		__irqstack_addr = .;
		__excstack_end = .;
		. = . +__excstack_size;
		. = ALIGN(16);
		__excstack_addr = .;
	} >sdram

	.pagetable :
	{
		. = ALIGN(16384);
		__page_table = .;
		. = . + 16384;
	} >sdram

	/DISCARD/ :
	{
		*(.ARM.exidx*)
		*(.ARM.extab*)
	}

}


