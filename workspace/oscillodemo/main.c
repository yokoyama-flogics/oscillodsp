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
 * Main Routine
 *
 * Written by Atsushi Yokoyama, Firmlogics (contact@flogics.com)
 */


#include <ti/sysbios/BIOS.h>
#include <ti/sysbios/hal/Hwi.h>
#include <ti/sysbios/knl/Task.h>
#include <ti/sysbios/knl/Clock.h>
#include "config.h"
#include "com.h"
#include "uart.h"
#include "oscillo.h"


char uart_readbuf[UART_READBUF_LEN];
char uart_writebuf[UART_WRITEBUF_LEN];


/**
 * Main Routine
 */
void main(void)
{
    /*
     * Initialize UART (serial port)
     */
    init_cic_interrupt(UART0_INTNUM, UART0_CIC, CIC0_UART0INT_EV, CIC_OUT_CH);
    uart_init(UART0, uart_readbuf, uart_writebuf, UART_READBUF_LEN,
        // UART_WRITEBUF_LEN, 115200, 16, UART0_INTNUM); // ok for Windows FTDI
        // UART_WRITEBUF_LEN, 854701, 13, UART0_INTNUM); // bad
        // UART_WRITEBUF_LEN, 986193, 13, UART0_INTNUM); // bad
        // UART_WRITEBUF_LEN, 1488095, 16, UART0_INTNUM); // bad
        // UART_WRITEBUF_LEN, 115200, 16, UART0_INTNUM); // ok
        UART_WRITEBUF_LEN, 2083333, 16, UART0_INTNUM); // ok for 1286 Mbytes
        // 3472222: error at 16 Mbytes (log9)
        // 2604167: error at 427 Mbytes (log10)

    /*
     * Launch RTOS scheduler
     */
    BIOS_start();
}

xdc_Void func_task_main(xdc_UArg uarg0, xdc_UArg uarg1)
{
    bool active;
    int ch0;
    int ch1;

    /*
     * XXX  The root cause is not known, but this is required to catch UART
     * interrupt.
     */
    Hwi_enableInterrupt(UART0_INTNUM);

    com_init();
    oscillo_init(1e6, 1e-3);

    ch0 = oscillo_config_ch("input", "volts", -4.0, 5.0);
    ch1 = oscillo_config_ch("output", "amperes", -3.0, 3.0);

    for (;;) {
        com_proc();

        active = Clock_getTicks() % 4000 < 2000;
        oscillo_pass_one(ch0, oscillo_get_demo1_value(active));
        oscillo_pass_one(ch1, oscillo_get_demo2_value(true));
    }

#ifdef DEBUG_UART
    for (;;) {
        uart_write(UART0, "Hello! ", 7);
        uart_flush(UART0);

        Task_sleep(100);
    }
#endif /* defined(DEBUG_UART) */

}
