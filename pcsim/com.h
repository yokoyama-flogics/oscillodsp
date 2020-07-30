/*
 * Communication handler between host and MCU, header file
 *
 * yokoyama@flogics.com
 */

#ifndef __COM_H__

#include "oscillodsp.pb.h"


int com_init(void);
int com_proc(void);
int com_send_msg(MessageToHost *reply);
int com_send_wave(Wave *wave);


#define __COM_H__
#endif /* ! defined(__COM_H__) */
