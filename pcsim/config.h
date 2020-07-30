#ifndef __CONFIG_H__

#include "oscillodsp.pb.h"

#define UART_READBUF_LEN    1024                            /* bytes */
#define UART_WRITEBUF_LEN   ((MessageToHost_size + 10) * 2) /* bytes */

#define NUM_UART            1
#define UART0               0

#define UART_CLK            166666666   /* Hz */
#define UART0_INTNUM        6           /* XXX  Change RTSC *.cfg file also */

/*
 * Refer Table 6-27. CIC0 Event Inputs (Secondary Interrupts for C66x CorePacs)
 * on the datasheet.
 *
 * XXX  These values are device specific.  You may need to change for other
 *      C66x devices.
 */
#define UART0_CIC           0        /* UARTINT is connected to CIC0 */
#define CIC0_UART0INT_EV    148      /* UARTINT is input event 148 of CIC0 */
#define CIC_OUT_CH          0        /* Output ch. number of CIC0 */


/*
 * Oscilloscope parameters
 */
typedef float sample_t;
typedef short buffer_t;
enum oscillo {
    LEN_BUFFER = 16384,
};
static const float HIST_MARGIN_X = 0.01f;
static const float HIST_MARGIN_Y = 0.015f;

#define __CONFIG_H__

#endif /* ! __CONFIG_H__ */
