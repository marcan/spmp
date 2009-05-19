#!/bin/bash

PREFIX=$SPMPDEV/bin/armel-eabi

INSTRUCTION="$@"

cat >/tmp/instr.s <<EOF 
	.ARM
	.text
	.globl _start
_start:
	$INSTRUCTION
EOF

$PREFIX-as -o /tmp/instr.o /tmp/instr.s || exit
$PREFIX-ld -Ttext=0 -o /tmp/instr.elf /tmp/instr.o || exit
$PREFIX-objcopy -O binary /tmp/instr.elf /tmp/instr.bin || exit

hexdump -vC /tmp/instr.bin
