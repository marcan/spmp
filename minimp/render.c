#include "types.h"
#include "render.h"
#include "gfx.h"
#include "uart.h"

#include "bunny.h"

u16 tx[BUNNY_VERTEX_COUNT];
u16 ty[BUNNY_VERTEX_COUNT];

extern u16 gfx_queue[131072];

#define FPM(x,y) ((s32)((((s64)(x)) * ((s64)(y))) >> 16))

static int llen = 1;
static u64 lpat = 1;

static u16 fg = 0xffff, bg = 0x0000;

void set_render_colors(u16 f, u16 b)
{
	fg = f;
	bg = b;
}

void set_render_style(int length, u64 pattern)
{
	llen = length;
	lpat = pattern;
}

void render_bunny(s32 m[3][3])
{
	int i;	
	//debug_printf("RENDER BUNNY\n");
	
	gfx_set_rop(ROP_PEN);
	gfx_set_color(bg);
	gfx_simple_fill(0,0,240,320);
	gfx_flush_queue();
	gfx_wait();

	gfx_set_color(fg);
	gfx_set_line_style(llen, lpat);
	
	for(i=0; i<BUNNY_VERTEX_COUNT; i++) {
		s32 x,y,z,nx,ny,nz;
		x = bunny_v[i][0];
		y = bunny_v[i][1];
		z = bunny_v[i][2];
		//debug_printf("Vertex %d %6x %6x %6x\n", i, x, y, z);
		nx = FPM(m[0][0],x) + FPM(m[0][1],y) + FPM(m[0][2],z);
		ny = FPM(m[1][0],x) + FPM(m[1][1],y) + FPM(m[1][2],z);
		nz = FPM(m[2][0],x) + FPM(m[2][1],y) + FPM(m[2][2],z);
		//debug_printf("       -> %6x %6x %6x\n", x, y, z);
		nx >>= 16;
		ny >>= 16;
		nx += 160;
		ny += 120;
		tx[i] = nx;
		ty[i] = ny;
		//debug_printf("Vertex %d: %d,%d\n", i, x, y);
	}
	u16 flags = 0;
	if(llen != 1 || lpat != 1)
		flags |= LINE_FLAG_STYLED;
	for(i=0; i<BUNNY_LINE_COUNT; i++) {
		u16 start, end;
		start = bunny_l[i][0];
		end = bunny_l[i][1];
		//debug_printf("Line %d: %d->%d %d,%d %d,%d\n", i, start, end, ty[start], tx[start], ty[end], tx[end]);
		gfx_simple_line(flags, ty[start], tx[start], ty[end], tx[end]);
	}
	gfx_flush_queue();
}
