#ifndef __COMDRV_H__

#include <xdc/std.h>

int comdrv_init(void);
void comdrv_restart(void);
int comdrv_read_protobuf(pb_byte_t *buf, int max_len);
int comdrv_write_block(const uint8_t *s, int len);
int comdrv_ensure_xmit_buffer_available(int len);
int comdrv_flush(void);
int comdrv_terminate(void);

#define __COMDRV_H__
#endif /* ! defined(__COMDRV_H__) */
