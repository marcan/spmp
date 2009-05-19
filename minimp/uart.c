/*
	minimp - port of MINI to the spmp305x
	uart

Copyright (C) 2008, 2009	Hector Martin "marcan" <marcan@marcansoft.com>

# This code is licensed to you under the terms of the GNU GPL, version 2;
# see file COPYING or http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
*/

#include "types.h"
#include "irq.h"
#include "start.h"
#include "vsprintf.h"
#include "string.h"
#include "utils.h"
#include "spmp3050.h"
#include "uart.h"
/*
// Receive a byte from the specified UART. Precondition is that the UART has been inited.
uint8_t UART_ReceiveByte(int uart){
        return UART_FIFO(uart);
}

int     UART_ReceiveBufferEmpty(int uart){
        if(!(UART_STATUS(uart) & UART_RX_VALID))
                return 0;
        return 1;
}*/


void uart_init(void)
{
	int uart = 1;
	volatile u8* uart_base = UART(uart);
	uart_base[0x0] = 0x68;
	uart_base[0x1] = 0x00;
	uart_base[0x4] = 0xD0;
	uart_base[0x5] = 0x11;
	uart_base[0xF] = 0x88;

	UART_ENABLE(uart);
}

void uart_sendbyte(int uart, char byte)
{
	while(UART_STATUS(uart) & UART_TX_BUSY);
	UART_FIFO(uart) = byte;
}

int uart_recvbyte(int uart, char *byte)
{
	if((UART_STATUS(uart) & UART_RX_VALID))
		return 0;
	*byte = UART_FIFO(uart);
	return 1;
}

u32 uart_sendbuffer_safe(void *buf, u32 len)
{
	const char *b = buf;
	u32 l = len;
	while(l--) {
		uart_sendbyte(1, *b++);
	}
	return len;
}

int uart_puts(const char *buf)
{
	int c = 0;
	while(*buf != 0) {
		if(*buf == '\n')
			uart_sendbyte(1, '\r');
		uart_sendbyte(1, *buf++);
		c++;
	}
	return c;
}

char uart_getchar(void)
{
	char c;
	while(!uart_recvbyte(1, &c));
	return c;
}

u32 uart_recvbuffer_safe(void *buf, u32 len)
{
	char *b = (char*)buf;
	u32 l = len;
	while(l--)
		*b++ = uart_getchar();
	return len;
}

#ifndef NDEBUG
int debug_printf(const char *fmt, ...)
{
	va_list args;
	char buffer[256];
	int i;

	va_start(args, fmt);
	i = vsprintf(buffer, fmt, args);
	va_end(args);

	return uart_puts(buffer);
}
#endif
