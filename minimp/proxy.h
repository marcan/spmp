#ifndef __PROXY_H__
#define __PROXY_H__

#include "types.h"

typedef enum {
	P_NOP = 0x000,				// System functions
	P_EXIT,
	P_CALL,

	P_WRITE32 = 0x100,			// Generic register functions
	P_WRITE16,
	P_WRITE8,
	P_READ32,
	P_READ16,
	P_READ8,
	P_SET32,
	P_SET16,
	P_SET8,
	P_CLEAR32,
	P_CLEAR16,
	P_CLEAR8,
	P_MASK32,
	P_MASK16,
	P_MASK8,

	P_MEMCPY32 = 0x200,			// Memory block transfer functions
	P_MEMCPY16,
	P_MEMCPY8,
	P_MEMSET32,
	P_MEMSET16,
	P_MEMSET8,

	P_DC_FLUSHRANGE = 0x300,	// Cache and memory ops
	P_DC_INVALRANGE,
	P_DC_FLUSHALL,
	P_IC_INVALALL,
	P_MAGIC_BULLSHIT,
	P_AHB_MEMFLUSH,
	P_MEM_PROTECT,
	
	P_NAND_READPAGE = 0x400,	// device operations
	P_NAND_WRITEPAGE,
	P_NAND_ERASEBLOCK,
	P_NAND_GETSTATUS
} ProxyOp;

#define S_OK		0
#define S_BADCMD	-1

typedef u32 (callfunc)(u32, u32, u32, u32);

typedef struct {
	u32 opcode;
	u32 args[6];
} ProxyRequest;

typedef struct {
	u32 opcode;
	s32 status;
	u32 retval;
} ProxyReply;

int proxy_process(ProxyRequest *request, ProxyReply *reply);

#endif
