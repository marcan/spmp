.arm

.globl _gfx_fifo_blast

.text

_gfx_fifo_blast:
	push {r4-r6, lr}
	/*
	 r0 = buffer pointer
	 r1 = buffer end
	 r2 = hw_tail
	 r3 = word from buffer
	 r4 = 0x1000c000
	*/
	 
	add r1, r0, r1, LSL#1
	cmp r1, r0
	beq __return

	mov r4, #0x10000000
	add r4, r4, #0xc000

__blast_loop:
	ldrh r3, [r0], #2

__wait_loop:
	ldrb r5, [r4, #0x18]
	sub r5, r2, r5
	and r5, r5, #0xff
	rsb r5, r5, #28
	cmp r5, r3, LSR #8
	/*blt __wait_loop*/

	mov r6, #1
	strb r6, [r4, #0x10]
	mov r5, #0
	strb r5, [r4, #0x06]
	strb r6, [r4, #0x01]

	movs r6, r3, LSR#8
	moveq r5, #0x2d
	orrne r5, r6, #0x40
	orrne r3, r3, #0x40

	strb r3, [r4]
	strb r5, [r4]

	add r6, r6, #1
	add r2, r2, r6
	and r2, r2, #0xff
	
__word_loop:
	ldrh r3, [r0], #2
	strb r3, [r4]
	mov r3, r3, LSR#8
	strb r3, [r4]
	subs r6, r6, #1
	bne __word_loop

	cmp r1, r0
	bhi __blast_loop

__return:
	and r0, r2, #0xFF
	pop {r4-r6, pc}
