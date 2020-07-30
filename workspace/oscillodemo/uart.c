/*
Copyright (c) 2020, Chubu University and Firmlogics

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

/*
 * UART Device Driver for TI C6678 EVM
 *
 * Written by Atsushi Yokoyama, Firmlogics (contact@flogics.com)
 */


#undef UART_DEBUG

#include <xdc/std.h>
#include <ti/sysbios/hal/Hwi.h>
#include <ti/sysbios/family/c66/tci66xx/CpIntc.h>
#include <assert.h>
#include <math.h>
#include "config.h"
#include "c6678_regs.h"
#include "uart.h"

static uart_context_t uart_context[NUM_UART];

/**
 * Low-level UART transmit routine
 *
 * While UART Tx FIFO can accept bytes and also there is a byte to transmit,
 * transfer bytes to Tx FIFO.
 *
 * General Notices:
 *    Must be called when UART interrupt is disabled or in UART ISR
 *
 * @param port is UART number (0 to 2 for C6748)
 * @param no_iir, non-zero if it is called without IIR indication
 */
static int uart_xmit(int port, int no_iir)
{
    uart_context_t *p;

#ifdef UART_DEBUG
    if (port != 0 && port != 2)
        for (;;)
            asm(" nop");
#endif /* UART_DEBUG */

    if (port < 0 || port >= NUM_UART)
        return -1;

    p = &uart_context[port];

    while ((UART_LSR(port) & (1 << 5)) != 0 &&
            p->writebuf_wr_pt != p->writebuf_rd_pt) {
        if (no_iir)
            p->tx_no_iir ++;
        UART_THR(port) = (p->writebuf)[p->writebuf_rd_pt];
        if (++ p->writebuf_rd_pt >= p->writebuf_len)
            p->writebuf_rd_pt = 0;
    }

    return 0;
}


/**
 * UART Interrupt Routine (ISR)
 *
 * Called by UART event (Tx, Rx, or some errors)
 *
 * General Notices:
 *    None
 *
 * @param arg is argument passed by SYS/BIOS which corresponds to UART port
 *        number
 */
void isr_uart(UArg arg)
{
    int port;
    uart_context_t *p;
    UInt32 iir;

    port = arg;

#ifdef UART_DEBUG
    if (port != 0 && port != 2)
        for (;;)
            asm(" nop");
#endif /* UART_DEBUG */

    if (port < 0 || port >= NUM_UART || ! uart_context[port].initialized)
        return;

    p = &uart_context[port];

    /*
     * (*1) In the manual SPRUH79A
     * Table 30-11. Interrupt Identification and Interrupt Clearing Information
     * For an overrun error, reading the line status register (LSR) clears the
     * interrupt. For a parity error, framing error, or break, the interrupt is
     * cleared only after all the erroneous data have been read.
     */
    while ((iir = UART_IIR(port) & 0xf) != 1) {
        switch (iir) {
        case 6:
            // Overrun error, parity error, framing error, or break is detected
            p->n_errors ++;
            while (UART_LSR(port) & 1)  // This RBR reading is required.
                (void) UART_RBR(port);  // Refer (*1) above.
            (void) UART_LSR(port);
            break;
        case 4:                     // Rx Trigger Level Reached
        case 12:                    // Rx Time-out
            p->readbuf[p->readbuf_wr_pt] = UART_RBR(port);
            if (++ p->readbuf_wr_pt >= p->readbuf_len)
                p->readbuf_wr_pt = 0;
            if (p->readbuf_wr_pt == p->readbuf_rd_pt)
                p->rx_overrun ++;
            break;
        case 2:                     // Tx FIFO is Empty
            uart_xmit(port, 0);
            break;
        default:                    // Shouldn't Happen
            p->n_errors ++;
            break;
        }
    }

    uart_xmit(port, 1);
}


/**
 * Return size of available space of write buffer
 *
 * General Notices:
 *    None
 *
 * @param port is UART number (0 to 2 for C6748)
 */
int uart_write_available(int port)
{
    int size;
    int ret_val;
    uart_context_t *p;

    if (port < 0 || port >= NUM_UART)
        return -1;

    p = &uart_context[port];

    size = p->writebuf_wr_pt - p->writebuf_rd_pt;
    if (size < 0)
        size += p->writebuf_len;

    ret_val = p->writebuf_len - size;

    /*
     * When writebuf_wr_pt and writebuf_rd_pt are equal, it is unclear if it is
     * buffer is empty or fully occupied.  So, we will reply one smaller value.
     */
    assert(ret_val > 0);
    ret_val -= 1;

    return ret_val;
}


/**
 * Store bytes into Tx software buffer
 *
 * General Notices:
 *    Need calling uart_flush() to send buffer contents toward UART hardware
 *
 * @param port is UART number (0 to 2 for C6748)
 * @param s is pointer to bytes
 * @param len is length of bytes
 */
int uart_write(int port, const uint8_t *s, int len)
{
    UInt key;
    int intnum;
    uart_context_t *p;

#ifdef UART_DEBUG
    if (port != 0 && port != 2)
        for (;;)
            asm(" nop");
#endif /* UART_DEBUG */

    if (port < 0 || port >= NUM_UART)
        return -1;

    if (len < 0)
        return -2;

    p = &uart_context[port];
    intnum = p->intnum;

    key = Hwi_disableInterrupt(intnum);
    while (len > 0) {
        p->writebuf[p->writebuf_wr_pt] = *s++;
        if (++ p->writebuf_wr_pt >= p->writebuf_len)
            p->writebuf_wr_pt = 0;
        if (p->writebuf_wr_pt == p->writebuf_rd_pt)
            p->tx_overrun ++;

        len --;
    }
    Hwi_restoreInterrupt(intnum, key);

    return 0;
}


/**
 * Flush Tx software buffer
 *
 * General Notices:
 *    None
 *
 * @param port is UART number (0 to 2 for C6748)
 */
int uart_flush(int port)
{
    UInt key;
    int intnum;
    uart_context_t *p;

#ifdef UART_DEBUG
    if (port != 0 && port != 2)
        for (;;)
            asm(" nop");
#endif /* UART_DEBUG */

    if (port < 0 || port >= NUM_UART)
        return -1;

    p = &uart_context[port];
    intnum = p->intnum;

    key = Hwi_disableInterrupt(intnum);
    uart_xmit(port, 0);
    Hwi_restoreInterrupt(intnum, key);

    return 0;
}


/**
 * Return number of available bytes in Rx software buffer to read
 *
 * General Notices:
 *    None
 *
 * @param port is UART number (0 to 2 for C6748)
 */
int uart_read_available(int port)
{
    int remain;
    uart_context_t *p;

#ifdef UART_DEBUG
    if (port != 0 && port != 2)
        for (;;)
            asm(" nop");
#endif /* UART_DEBUG */

    if (port < 0 || port >= NUM_UART)
        return 0;                       // XXX  Assumes there is no error

    p = &uart_context[port];

    remain = p->readbuf_wr_pt - p->readbuf_rd_pt;
    if (remain < 0)
        remain += p->readbuf_len;

    return remain;
}


/**
 * Read a character from Rx software buffer
 *
 * General Notices:
 *    None
 *
 * @param port is UART number (0 to 2 for C6748)
 * @param no_wait, when non-zero, promptly returns even if read-buffer is empty
 */
int uart_read_nowait(int port, int no_wait)
{
    int c;
    uart_context_t *p;

#ifdef UART_DEBUG
    if (port != 0 && port != 2)
        for (;;)
            asm(" nop");
#endif /* UART_DEBUG */

    if (port < 0 || port >= NUM_UART)
        return -2;

    p = &uart_context[port];

    if (no_wait) {
        if (! uart_read_available(port))
            return -1;
    } else {
        while (uart_read_available(port) == 0)
            ;
    }

    c = p->readbuf[p->readbuf_rd_pt];
    if (++ p->readbuf_rd_pt >= p->readbuf_len)
        p->readbuf_rd_pt = 0;

    return (int) c;
}


/**
 * Initialize UART
 *
 * Refer Chapter 30 of SPRUH79A
 *
 * General Notices:
 *    Return -1 if some argument is incorrect (or out of range)
 *    To leave a uart_context uninitialized, pass NULL as readbuf
 *
 * @param port is UART number (0 to 2 for C6748)
 * @param readbuf is pointer to UART read circular buffer
 * @param writebuf is pointer to UART write circular buffer
 * @param readbuf_len is length of assigned read buffer
 * @param writebuf_len is length of assigned write buffer
 * @param bitrate is communication speed (e.g. 9600, 115200 etc.)
 * @param div is pre-divisor value (13 or 16)
 * @param intnum is interrupt number corresponds to the UART port
 */
int uart_init(int port, char *readbuf, char *writebuf,
    int readbuf_len, int writebuf_len, int bitrate, int div, int intnum)
{
    int dl_val;
    uart_context_t *p;

#ifdef UART_DEBUG
    if (port == 1 && readbuf == NULL) {
        ;//
    } else if (port != 0 && port != 2) {
        for (;;)
            asm(" nop");
    }
#endif /* UART_DEBUG */

    if (port < 0 || port >= NUM_UART)
        return -1;

    if (div != 13 && div != 16)
        return -2;

    p = &uart_context[port];

    p->initialized = 1;
    p->readbuf_len = readbuf_len;
    p->writebuf_len = writebuf_len;
    p->n_errors = 0;
    p->rx_overrun = 0;
    p->tx_no_iir = 0;
    p->tx_overrun = 0;
    p->readbuf_rd_pt = 0;
    p->readbuf_wr_pt = 0;
    p->writebuf_rd_pt = 0;
    p->writebuf_wr_pt = 0;
    p->readbuf = readbuf;
    p->writebuf = writebuf;
    p->intnum = intnum;

    if (readbuf == NULL) {
        p->initialized = 0;
        p->reg_base = 0;
        return 0;
    }

    p->reg_base = UART_REG_BASES[port];

    UART_PWREMU_MGMT(port) = 0 << 14    // UTRST
                           | 0 << 13    // URRST
                           | 1 << 0;    // FREE

    UART_MDR(port) = (div == 13) ? 1 : 0;   // OSM_SEL

    /*
     * Refer Table 30-1. Baud Rate Examples for 150-MHZ UART Input Clock and 16x
     * Over-sampling Mode of SPRUH79A
     */
    dl_val = (int) floorf((float) UART_CLK / div / bitrate + 0.5F);
    UART_DLL(port) = (dl_val >> 0) & 0xff;  // BAUDRATE DIVISOR (LO)
    UART_DLH(port) = (dl_val >> 8) & 0xff;  // BAUDRATE DIVISOR (HIGH)

    UART_FCR(port) = 0 << 6             // RXFIFTL
                   | 1 << 3             // DMAMODE1
                   | 1 << 2             // TXCLR
                   | 1 << 1             // RXCLR
                   | 1 << 0;            // FIFOEN

    UART_LCR(port) = 0 << 6             // BC
                   | 0 << 5             // SP
                   | 0 << 4             // EPS
                   | 0 << 3             // PEN
                   | 0 << 2             // STB
                   | 3 << 0;            // WLS

    UART_MCR(port) = 0 << 5             // AFE
                   | 0 << 4             // LOOP
                   | 0 << 1;            // RTS

    UART_IER(port) = 1 << 2             // ELSI
                   | 1 << 1             // ETBEI
                   | 1 << 0;            // ERBI

    UART_PWREMU_MGMT(port) = 1 << 14    // UTRST
                           | 1 << 13    // URRST
                           | 1 << 0;    // FREE

    return 0;
}


/**
 * Initialize CIC controller
 *
 * @param int_vec is interrupt vector number to the DSP core
 * @param cic is ID of CIC to use
 * @param cic_event_in is event ID of CIC input
 * @param cic_out_ch is internal channel ID of the CIC
 */
int init_cic_interrupt(int int_vec, int cic, int cic_event_in, int cic_out_ch)
{
    int event_id;
    Hwi_Params params;

    // Map the System Interrupt to the ISR Handler.
    CpIntc_dispatchPlug(cic_event_in, (CpIntc_FuncPtr) isr_uart, UART0, TRUE);

    // We map a system interrupt to a Host Interrupt.
    CpIntc_mapSysIntToHostInt(cic, cic_event_in, cic_out_ch);

    // Enable the Host Interrupt.
    CpIntc_enableHostInt(cic, cic_out_ch);

    // Enable the System Interrupt
    CpIntc_enableSysInt(cic, cic_event_in);

    // Get the event id associated with the host interrupt.
    event_id = CpIntc_getEventId(cic_out_ch);

    Hwi_Params_init(&params);

    // Host interrupt value
    params.arg = cic_out_ch;

    // Event id for your host interrupt
    params.eventId = event_id;

    // Enable the Hwi
    params.enableInt = TRUE;

    /* This plugs the interrupt vector and the ISR function.  When using
     * CpIntc, you must plug the Hwi fxn with CpIntc_dispatch so it knows how
     * to process the CpIntc interrupts.
     */
    Hwi_create(int_vec, &CpIntc_dispatch, &params, NULL);

    return 0;
}
