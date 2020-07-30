#ifndef __UART_H__

#include <xdc/std.h>


#define UART_RBR(x)     (*(volatile int*) (uart_context[x].reg_base + 0x00))
#define UART_THR(x)     (*(volatile int*) (uart_context[x].reg_base + 0x00))
#define UART_IER(x)     (*(volatile int*) (uart_context[x].reg_base + 0x04))
#define UART_IIR(x)     (*(volatile int*) (uart_context[x].reg_base + 0x08))
#define UART_FCR(x)     (*(volatile int*) (uart_context[x].reg_base + 0x08))
#define UART_LCR(x)     (*(volatile int*) (uart_context[x].reg_base + 0x0c))
#define UART_MCR(x)     (*(volatile int*) (uart_context[x].reg_base + 0x10))
#define UART_LSR(x)     (*(volatile int*) (uart_context[x].reg_base + 0x14))
#define UART_DLL(x)     (*(volatile int*) (uart_context[x].reg_base + 0x20))
#define UART_DLH(x)     (*(volatile int*) (uart_context[x].reg_base + 0x24))
#define UART_PWREMU_MGMT(x) (*(volatile int*) (uart_context[x].reg_base + 0x30))
#define UART_MDR(x)     (*(volatile int*) (uart_context[x].reg_base + 0x34))

typedef struct uart_context {
    int initialized;
    int readbuf_len;
    int writebuf_len;
    volatile int n_errors;          // UART error events counter
    volatile int rx_overrun;        // Number of Rx overrun
    volatile int tx_no_iir;         // How many uart_xmit(no_iir = 1) occurred
    volatile int tx_overrun;        // Number of Tx overrun
    int readbuf_rd_pt;
    volatile int readbuf_wr_pt;
    volatile int writebuf_rd_pt;
    int writebuf_wr_pt;
    volatile char *readbuf;
    volatile char *writebuf;
    unsigned int reg_base;
    int intnum;
} uart_context_t;

void isr_uart(UArg arg);
int uart_write_available(int port);
int uart_write(int port, const uint8_t *s, int len);
int uart_flush(int port);
int uart_read_available(int port);
int uart_read_nowait(int port, int no_wait);
int uart_init(int port, char *readbuf, char *writebuf,
    int readbuf_len, int writebuf_len, int bitrate, int div, int intnum);
int init_cic_interrupt(int int_vec, int cic, int cic_event_in, int cic_out_ch);

#define __UART_H__

#endif /* ! __UART_H__ */
