#include "types.h"
#include "utils.h"
#include "gfx.h"
#include "uart.h"

static u8 hw_tail;

u16 gfx_queue[131072];

static u16 *gfx_head;

static u16 gfx_regs[0x1c];

#define REG_COUNT 0x1c

typedef enum {
	/* 0x00 */ GR_SRC_LO = 0x00,
	/* 0x01 */ GR_SRC_HI,
	/* 0x02 */ GR_SRC_STRIDE,
	/* 0x03 */ GR_SRC_X,
	/* 0x04 */ GR_SRC_Y,
	/* 0x05 */ GR_FB_LO,
	/* 0x06 */ GR_FB_HI,
	/* 0x07 */ GR_FB_STRIDE,
	/* 0x08 */ GR_FB_HEIGHT,
	/* 0x09 */ GR_DST_X,
	/* 0x0a */ GR_DST_Y,
	/* 0x0b */ GR_WIDTH,
	/* 0x0c */ GR_HEIGHT, GR_LINE_STYLE_LENGTH = GR_HEIGHT,
	/* 0x0d */ GR_ROP, GR_FLIP_FLAGS = GR_ROP,
	/* 0x0e */ GR_PEN_COLOR,
	/* 0x0f */ GR_STIPPLE_0, GR_LINE_STYLE_0 = GR_STIPPLE_0, GR_SHADE_X_R = GR_STIPPLE_0,
	/* 0x10 */ GR_STIPPLE_1, GR_LINE_STYLE_1 = GR_STIPPLE_1, GR_SHADE_X_G = GR_STIPPLE_1,
	/* 0x11 */ GR_STIPPLE_2, GR_LINE_STYLE_2 = GR_STIPPLE_2, GR_SHADE_X_B = GR_STIPPLE_2,
	/* 0x12 */ GR_STIPPLE_3, GR_LINE_STYLE_3 = GR_STIPPLE_3, GR_SHADE_Y_R = GR_STIPPLE_3,
	/* 0x13 */ GR_CLUT_LO, GR_SHADE_Y_G = GR_CLUT_LO,
	/* 0x14 */ GR_CLUT_HI, GR_SHADE_Y_B = GR_CLUT_HI,
	/* 0x15 */ _GR_UNK1,
	/* 0x16 */ _GR_UNK2,
	/* 0x17 */ _GR_UNK3,
	/* 0x18 */ _GR_UNK4,
	/* 0x19 */ GR_BLEND,
	/* 0x1a */ GR_BIT_MASK,
	/* 0x1b */ _GR_UNK5,
	/* 0x1c */ GR_DRAW
} gfx_reg;

#define DRAW_BLIT 0
#define DRAW_LINE 2
#define DRAW_SHADE 3

static inline void queue_put(u32 value) {
	*gfx_head++ = value;
	// TODO: should be a circular buffer
}

static inline void pushdraw(u32 a) {
	queue_put(GR_DRAW);
	queue_put(a);
}

static inline void push1(gfx_reg reg, u32 a) {
	queue_put(reg);
	queue_put(a); gfx_regs[reg] = a;
}
static inline void push2(gfx_reg reg, u32 a, u32 b) {
	queue_put(0x0100 | reg);
	queue_put(a); gfx_regs[reg] = a;
	queue_put(b); gfx_regs[reg+1] = b;
}
static inline void push3(gfx_reg reg, u32 a, u32 b, u32 c) {
	queue_put(0x0200 | reg);
	queue_put(a); gfx_regs[reg] = a;
	queue_put(b); gfx_regs[reg+1] = b;
	queue_put(c); gfx_regs[reg+2] = c;
}
static inline void push4(gfx_reg reg, u32 a, u32 b, u32 c, u32 d) {
	queue_put(0x0300 | reg);
	queue_put(a); gfx_regs[reg] = a;
	queue_put(b); gfx_regs[reg+1] = b;
	queue_put(c); gfx_regs[reg+2] = c;
	queue_put(d); gfx_regs[reg+3] = d;
}

void gfx_init(void)
{
	write8(0x1000c007, 1);
	while(read8(0x1000c015) & 1);
	hw_tail = read8(0x1000c018);
	gfx_head = gfx_queue;
	memset16(gfx_queue, 0, 131072);
	memset16(gfx_regs, 0, REG_COUNT);
	// clear all registers
	gfx_queue[0] = (REG_COUNT-1) << 8;
	gfx_sendfifobuf(gfx_queue, 1 + 0x1c);
}

u8 _gfx_fifo_blast(u16 *buf, int count, u8 hw_tail);

void gfx_sendfifobuf(u16 *buf, int count)
{
	hw_tail = _gfx_fifo_blast(buf, count, hw_tail);
#if 0
	u16 *end = buf+count;
	while(buf != end) {
		s32 fifo_free;
		u32 cval = *buf++;
		s32 count = (cval >> 8) & 0xFF;
		u32 reg = cval & 0xFF;
		do {
			fifo_free = 29 - ((hw_tail - read8(0x1000c018)) & 0xff);
		} while(fifo_free < count);
		write8(0x1000c010, 1);
		write8(0x1000c006, 0);
		write8(0x1000c001, 1);
		if(count == 1) {
			write8(0x1000c000, reg);
			write8(0x1000c000, 0x2d);
		} else {
			write8(0x1000c000, 0x40 | reg);
			write8(0x1000c000, 0x40 | (count-1));
		}
		hw_tail += count;
		while(count--) {
			u16 value = *buf++;
			write8(0x1000c000, value & 0xff);
			write8(0x1000c000, value >> 8);
		}
	}
#endif
}

void gfx_flush_queue(void) {
	gfx_sendfifobuf(gfx_queue, gfx_head - gfx_queue);
	gfx_head = gfx_queue;
}

void gfx_set_line_style(int length, u64 style)
{
	if(length <= 16)
		push1(GR_LINE_STYLE_0, style);
	else if(length <= 32)
		push2(GR_LINE_STYLE_0, style, style>>16);
	else if(length <= 48)
		push3(GR_LINE_STYLE_0, style, style>>16, style>>32);
	else
		push4(GR_LINE_STYLE_0, style, style>>16, style>>32, style>>48);
	push1(GR_LINE_STYLE_LENGTH, length-1);
}

void gfx_simple_line(u16 flags, u16 sx, u16 sy, u16 dx, u16 dy)
{
	if(sx != gfx_regs[GR_SRC_X] || sy != gfx_regs[GR_SRC_Y])
		push2(GR_SRC_X, sx, sy);
	push2(GR_DST_X, dx, dy);
	pushdraw(DRAW_LINE | flags);
}

void gfx_simple_fill(u16 x, u16 y, u16 w, u16 h)
{
	push4(GR_DST_X, x, y, w, h);
	pushdraw(DRAW_BLIT);
}

void gfx_set_rop(u8 rop)
{
	if(rop != (gfx_regs[GR_ROP]&0xff))
		push1(GR_ROP, (gfx_regs[GR_ROP]&0xFF00) | rop);
}
void gfx_set_color(u16 color)
{
	if(color != gfx_regs[GR_PEN_COLOR])
		push1(GR_PEN_COLOR, color);
}

void gfx_wait(void)
{
	while(read8(0x1000c015) & 1);
}
