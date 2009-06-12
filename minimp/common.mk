ifeq ($(strip $(SPMPDEV)),)
$(error "Set SPMPDEV in your environment.")
endif

PREFIX = $(SPMPDEV)/bin/armel-eabi-

CFLAGS += -march=armv5te
CFLAGS += -fomit-frame-pointer -ffunction-sections
CFLAGS += -Wall -Wextra -O3 -pipe
ASFLAGS =
LDFLAGS = -ffreestanding -n -nostartfiles -nodefaultlibs -Wl,-gc-sections

AR = $(PREFIX)ar
AS = $(PREFIX)as
CC = $(PREFIX)gcc
CXX = $(PREFIX)g++
LD = $(PREFIX)ld
OBJCOPY = $(PREFIX)objcopy
RANLIB = $(PREFIX)ranlib
STRIP = $(PREFIX)strip

ifeq ($(NOMAPFILE),)
LDFLAGS += -Wl,-Map,$(TARGET).map
endif

ifneq ($(LDSCRIPT),)
LDFLAGS += -Wl,-T$(LDSCRIPT)
endif

DEPDIR = .deps

all: $(TARGET)

$(TARGET): $(OBJS)
	@echo "  LINK      $@"
	@$(CC) $(LDFLAGS) $(OBJS) $(LIBS) -o $@

ifneq ($(LDSCRIPT),)
$(TARGET): $(LDSCRIPT)
endif

%.o: %.c
	@echo "  COMPILE   $<"
	@mkdir -p $(DEPDIR)
	@$(CC) $(CFLAGS) $(DEFINES) -Wp,-MMD,$(DEPDIR)/$(*F).d,-MQ,"$@",-MP -c $< -o $@

%.o: %.s
	@echo "  ASSEMBLE  $<"
	@$(CC) $(CFLAGS) $(DEFINES) $(ASFLAGS) -c $< -o $@

%.o: %.S
	@echo "  ASSEMBLE  $<"
	@$(CC) $(CFLAGS) $(DEFINES) $(ASFLAGS) -c $< -o $@

clean:
	rm -rf $(DEPDIR)
	rm -f $(TARGET) $(TARGET).map $(OBJS)

-include $(DEPDIR)/*

.PHONY: clean

