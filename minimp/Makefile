
LDSCRIPT = mini.ld
LIBS = -lgcc

TARGET = miniboot.elf
TARGET_BIN = miniboot.bin
OBJS = start.o main.o vsprintf.o string.o uart.o memory.o memory_asm.o \
	utils_asm.o utils.o panic.o proxy.o uartproxy.o\
	irq.o irq_asm.o exception.o exception_asm.o ldhack.o

all: $(TARGET_BIN)

$(TARGET_BIN): $(TARGET)
	@echo  "  OBJCOPY   $@"
	@$(OBJCOPY) -O binary $< $@

upload: $(TARGET_BIN)
	@$(SPMPDEV)/bin/spload $<
	
clean: myclean

myclean:
	-rm -f $(TARGET_BIN)

include common.mk

