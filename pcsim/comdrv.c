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
 * UART Abstraction Layer for POSIX
 *
 * Written by Atsushi Yokoyama, Firmlogics (contact@flogics.com)
 */


#undef DEBUG_READ
#define PTYNAME_FILE    "ptyname.txt"

#include <stdio.h>
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/select.h>
#include "pb.h"
#include "config.h"
#include "comdrv.h"
#include "oscillo.h"


static int fd_tty;


/**
 * Initialize comdrv
 */
int comdrv_init(void)
{
    extern int posix_openpt(int flags);
    extern char *ptsname(int fd);
    extern int grantpt(int fd);
    extern int unlockpt(int fd);
    FILE *fp;

    fd_tty = posix_openpt(O_RDWR | O_NOCTTY);
    printf("ptsname: %s\n", ptsname(fd_tty));

    fp = fopen(PTYNAME_FILE, "w");
    fprintf(fp, "%s", ptsname(fd_tty));
    fclose(fp);

    grantpt(fd_tty);
    unlockpt(fd_tty);

    return 0;
}


/**
 * Restart comdrv
 */
void comdrv_restart(void)
{
    printf("cmp_proc(): len < -1\n");
    fflush(stdout);
    close(fd_tty);
    oscillo_reinit();
    comdrv_init();
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
    char c;
    int len;        // Only 16 LSB are used to store message length
    int ret;        // Return-value.  Length or error code
    fd_set rfds;
    struct timeval tv;

    /*
     * If no bytes are available to read, return here
     */
    tv.tv_sec = 0;
    tv.tv_usec = 0;

    FD_ZERO(&rfds);
    FD_SET(fd_tty, &rfds);

    ret = select(fd_tty + 1, &rfds, NULL, NULL, &tv);
    if (ret == 0)
        return -1;

    ret = read(fd_tty, &c, 1);
    len = (int) c << 8;   // Store it as upper part of length

    read(fd_tty, &c, 1);
    len |= (int) c;  // Then lower part of length

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
    read(fd_tty, buf, len);

#ifdef DEBUG_READ
    if (len > 16)
        len = 16;
    for (int i = 0; i < len; i ++)
        printf("%02x ", buf[i]);
    printf("\n");
#endif /* defined(DEBUG_READ) */

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
    return write(fd_tty, s, len);
}


/**
 * Ensure UART transmit buffer has enough room
 */
int comdrv_ensure_xmit_buffer_available(int len)
{
    /*
     * In POSIX environment, write() usually blocks so we do nothing here.
     */
    return 0;
}


/**
 * Flush UART transmit buffer
 */
int comdrv_flush(void)
{
    /*
     * POSIX write() doesn't require flush.
     */
    return 0;
}


/**
 * Terminate simulator
 */
int comdrv_terminate(void)
{
    exit(0);
}
