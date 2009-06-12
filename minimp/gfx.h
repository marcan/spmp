#ifndef __GFX_H__
#define __GFX_H__

#define ROP_BLACKNESS 0x00
#define ROP_SRC 0xCC
#define ROP_DST 0xAA
#define ROP_PEN 0xF0
#define ROP_WHITENESS 0xFF

#define LINE_FLAG_STYLED 0x800
#define LINE_STYLE_RESET 0x200

void gfx_init(void);
void gfx_sendfifobuf(u16 *buf, int count);
void gfx_flush_queue(void);
void gfx_set_rop(u8 rop);
void gfx_set_color(u16 color);
void gfx_simple_line(u16 flags, u16 sx, u16 sy, u16 dx, u16 dy);
void gfx_simple_fill(u16 x, u16 y, u16 w, u16 h);
void gfx_set_line_style(int length, u64 style);
void gfx_wait(void);
#endif