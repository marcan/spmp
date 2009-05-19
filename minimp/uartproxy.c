#include "types.h"
#include "proxy.h"
#include "uart.h"
#include "string.h"
#include "start.h"

typedef struct {
	u32 type;
	union {
		ProxyRequest prequest;
		struct {
			u32 addr;
			u32 size;
			u32 dchecksum;
		} mrequest;
	};
	u32 checksum;
} UartRequest;

typedef struct {
	u32 type;
	u32 status;
	union {
		ProxyReply preply;
		struct {
			u32 dchecksum;
		} mreply;
	};
	u32 checksum;
} UartReply;

#define REQ_NOP			0x00AA55FF
#define REQ_PROXY		0x01AA55FF
#define REQ_MEMREAD		0x02AA55FF
#define REQ_MEMWRITE	0x03AA55FF

#define ST_OK		0
#define ST_BADCMD	-1
#define ST_INVAL	-2
#define ST_XFRERR	-3
#define ST_CRCERR	-4

// I just totally pulled this out of my arse
u32 checksum(void *start, u32 length) {
	u32 sum = 0xDEADBEEF;
	u8 *d = (u8*)start;

	while(length--) {
		sum *= 31337;
		sum += (*d++) ^ 0x5A;
	}
	return sum ^ 0xADDEDBAD;
}

void uartproxy_run(void) {
	int running = 1;
	int c;
	u32 bytes;

	UartRequest request;
	UartReply reply;

	while(running) {
		c = uart_getchar();
		if(c != 0xFF)
			continue;
		c = uart_getchar();
		if(c != 0x55)
			continue;
		c = uart_getchar();
		if(c != 0xAA)
			continue;
		c = uart_getchar();
		if(c < 0)
			continue;
		memset(&request, 0, sizeof(request));
		request.type = 0x00AA55FF | ((c&0xff)<<24);
		bytes = uart_recvbuffer_safe((&request.type) + 1,sizeof(request) - 4);
		if (bytes != (sizeof(UartRequest) - 4))
			continue;
		if(checksum(&request, sizeof(request) - 4) != request.checksum)
			continue;

		memset(&reply, 0, sizeof(reply));
		reply.type = request.type;
		reply.status = ST_OK;

		switch(request.type) {
			case REQ_NOP:
				break;
			case REQ_PROXY:
				running = proxy_process(&request.prequest, &reply.preply);
				break;
			case REQ_MEMREAD:
				reply.mreply.dchecksum = checksum((void*)request.mrequest.addr, request.mrequest.size);
				break;
			case REQ_MEMWRITE:
				bytes = uart_recvbuffer_safe((void*)request.mrequest.addr, request.mrequest.size);
				if(bytes != request.mrequest.size) {
					reply.status = ST_XFRERR;
					break;
				}
				reply.mreply.dchecksum = checksum((void*)request.mrequest.addr, request.mrequest.size);
				if(reply.mreply.dchecksum != request.mrequest.dchecksum)
					reply.status = ST_XFRERR;
				break;
			default:
				reply.status = ST_BADCMD;
				break;
		}
		reply.checksum = checksum(&reply, sizeof(reply) - 4);
		uart_sendbuffer_safe(&reply, sizeof(reply));

		if((request.type == REQ_MEMREAD) && (reply.status == ST_OK)) {
			uart_sendbuffer_safe((void*)request.mrequest.addr, request.mrequest.size);
		}
	}
}

