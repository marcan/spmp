#define	IO_BASE			((volatile void*)0x10000000)

#define DEV_ENABLE		(*(volatile uint8_t*)(IO_BASE + 0x1100))
#define DEV_ENABLE_OUT	(*(volatile uint8_t*)(IO_BASE + 0x1108))	// For lack of a better term...

#define UART_BASE		(IO_BASE + 0x1800)
#define	UART(n)			(UART_BASE + (n << 5))
#define UART_FIFO(n)	(*(volatile uint8_t*)(UART(n) + 0x02))
#define UART_STATUS(n)	(*(volatile uint8_t*)(UART(n) + 0x0A))
#define UART_ENABLE(n)	(*(volatile uint8_t*)(UART_BASE + 0x80)) |= (1 << n)
#define UART_DISABLE(n)	(*(volatile uint8_t*)(UART_BASE + 0x80)) &= ~(1 << n)

#define UART_TX_BUSY	0x02
#define UART_RX_VALID	0x04

#define GPIO_BASE		(IO_BASE + 0xB000)
#define GPIO_A			(GPIO_BASE + 0x60)
#define GPIO_A_DIR		(*(volatile uint32_t*)(GPIO_A + 0x4))
#define GPIO_A_OUT		(*(volatile uint32_t*)(GPIO_A + 0x8))
#define GPIO_A_IN		(*(volatile uint32_t*)(GPIO_A + 0xC))

#define GPIO_B			(GPIO_BASE + 0xE0)
#define GPIO_B_DIR		(*(volatile uint32_t*)(GPIO_B + 0x4))
#define GPIO_B_OUT		(*(volatile uint32_t*)(GPIO_B + 0x8))
#define GPIO_B_IN		(*(volatile uint32_t*)(GPIO_B + 0xC))

#define GPIO_DISABLE	(*(volatile uint32_t*)(GPIO_BASE + 0x320))

#define LCD_BASE		(IO_BASE + 0xA000)
#define LCD_DATA		(*(volatile uint16_t*)(LCD_BASE + 0x196))
// Extended data register. We have an 18 bit bus, and the upper two are here. Bits 3 and 2 (!)
#define LCD_DATA_EXT	(*(volatile uint8_t*)(LCD_BASE + 0xE4))
#define LCD_CTRL		(*(volatile uint8_t*)(LCD_BASE + 0x195))
#define	LCD_nRS			0x04
#define LCD_CS			0x20
#define LCD_WR			0x40

#define LCD_DATA_DIR	(*(volatile uint8_t*)(LCD_BASE + 0x192))
#define LCD_OUT			0x20

#define LCD_RESET_REG	(*(volatile uint8_t*)(LCD_BASE + 0x1B1))
#define LCD_RESET		0x80

#define DEV_ENABLE              (*(volatile uint8_t*)(IO_BASE + 0x1100))

#define IRQ_FLAG_1		(*(volatile uint8_t*)(IO_BASE + 0x10c0))
#define IRQ_FLAG_2              (*(volatile uint8_t*)(IO_BASE + 0x10c4))
#define IRQ_MASK_1              (*(volatile uint8_t*)(IO_BASE + 0x1310))
#define IRQ_MASK_2              (*(volatile uint8_t*)(IO_BASE + 0x1314))



