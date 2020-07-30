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
 * UART Abstraction Layer for DSP
 *
 * Written by Atsushi Yokoyama, Firmlogics (contact@flogics.com)
 */


#include "pb.h"
#include "config.h"
#include "comdrv.h"
#include "uart.h"


/**
 * Initialize comdrv
 */
int comdrv_init(void)
{
    return 0;
}


/**
 * Restart comdrv
 */
void comdrv_restart(void)
{
    /*
     * Not defined how to restart
     */
    for (;;)
        asm(" nop");
}


/**
 * Read a protobuf msg from UART
 *
 * @return -1 if no bytes are available, -2 if null message received,
 *         -3 if buf is too short to store message, otherwise length of
 *         received message
 */
int comdrv_read_protobuf(pb_byte_t *buf, int max_len)
{
    int c;
    int i;
    int len;        // Only 16 LSB are used to store message length
    int ret;        // Return-value.  Length or error code

    c = uart_read_nowait(UART0, TRUE);

    /*
     * If no bytes are available to read, return here
     */
    if (c < 0)
        return -1;

    len = (c & 0xff) << 8;   // Store it as upper part of length

    len |= uart_read_nowait(UART0, FALSE) & 0xff;  // Then lower part of length

    ret = len;  // Set length as return value, but may be overwritten later

    /*
     * If message is null (or len == 0), return here.
     */
    if (len == 0)
        return -2;

    /*
     * If length is longer than given buffer, read message but NOT store
     * into the buffer.
     */
    if (len > max_len)
        ret = -3;

    /*
     * Actually read message bytes from UART.  Never store bytes which don't
     * fit into the buffer.
     */
    for (i = 0; i < len; i ++) {
        if (i < max_len)
            buf[i] = uart_read_nowait(UART0, FALSE);
    }

    return ret;
}


/**
 * Write a block of bytes to UART.
 *
 * @return -1 if no bytes are available, -2 if null message received,
 *         -3 if buf is too short to store message, otherwise length of
 *         received message
 */
int comdrv_write_block(const uint8_t *s, int len)
{
    return uart_write(UART0, s, len);
}


/**
 * Ensure UART transmit buffer has enough room
 */
int comdrv_ensure_xmit_buffer_available(int len)
{
    /*
     * Wait until enough space in UART transmit buffer is available
     */
    while (uart_write_available(UART0) < len)
        asm(" nop");

    return 0;
}


/**
 * Flush UART transmit buffer
 */
int comdrv_flush(void)
{
    return uart_flush(UART0);
}


/**
 * Terminate simulator
 */
int comdrv_terminate(void)
{
    // Not implemented

    return 0;
}
