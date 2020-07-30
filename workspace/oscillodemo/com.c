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
 * Protobuf Communication Handler between host PC and DSP
 *
 * Written by Atsushi Yokoyama, Firmlogics (contact@flogics.com)
 */


#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include "common.h"
#include "com.h"
#include "comdrv.h"
#include "oscillo.h"
#include "pb_encode.h"
#include "pb_decode.h"


#define MAX(a, b)   ((a) > (b) ? (a) : (b))


static pb_byte_t stream_buf[MAX(MessageToDSP_size, MessageToHost_size) + 1];
static MessageToDSP msg;
static MessageToHost reply;

int debug_com_ct = 0;   // XXX

int debug_id;   // XXX
int debug_port; // XXX
int debug_val;  // XXX

/**
 * Reply a message to host
 *
 * @return -1 if failed to encode reply
 */
static int send_reply(MessageToHost *reply)
{
    return com_send_msg(reply);
}


/**
 * Acknowledge a message from host (reply to host)
 *
 * @return -1 if failed to encode reply
 */
static int ack(uint32_t id, ErrorCode err)
{
    memset(&reply, 0, sizeof(reply));

    reply.id = id;
    reply.payload.ack.err = err;
    reply.which_payload = MessageToHost_ack_tag;

    return send_reply(&reply);
}


/**
 * EchoRequest command handler.
 */
static int cmd_echoreq(uint32_t id, const EchoRequest *echoreq)
{
    char s[80];

    memset(&reply, 0, sizeof(reply));

    snprintf(s, sizeof(s) - 1, "EchoReq: %d %s\r\n",
            (int) id, echoreq->content);

    debug_com_ct ++;

    reply.id = id;
    memcpy(
            reply.payload.echorep.content,
            echoreq->content,
            sizeof(echoreq->content));

    reply.which_payload = MessageToHost_echorep_tag;

    return send_reply(&reply);
}


/**
 * Send Wave data to host
 */
static int cmd_getwave(uint32_t id)
{
    memset(&reply, 0, sizeof(reply));

    reply.id = id;
    oscillo_get_waves(&reply.payload.wavegroup);
    reply.which_payload = MessageToHost_wavegroup_tag;
    send_reply(&reply);

    return 0;
}


/**
 * Configure oscillo modes
 */
static int cmd_config(uint32_t id, Configure config)
{
    int ret;

    memset(&reply, 0, sizeof(reply));

    reply.id = id;
    ret = oscillo_config(config, &reply.payload.configreply);
    reply.payload.configreply.err =
        (ret == 0) ? ErrorCode_NoError : ErrorCode_ConfigError;
    reply.which_payload = MessageToHost_configreply_tag;
    send_reply(&reply);

    return 0;
}


/**
 * Decode a message from host
 */
static int decode_msg(const pb_byte_t *buf, int len)
{
    pb_istream_t stream = pb_istream_from_buffer(buf, len);
    bool status;
    int err = 0;

    (void) err;
    (void) ack;

    memset(&msg, 0, sizeof(msg));
    status = pb_decode(&stream, MessageToDSP_fields, &msg);

    switch (msg.which_payload) {
        case MessageToDSP_echoreq_tag:
            cmd_echoreq(msg.id, &msg.payload.echoreq);
            break;
        case MessageToDSP_config_tag:
            cmd_config(msg.id, msg.payload.config);
            break;
        case MessageToDSP_getwave_tag:
            cmd_getwave(msg.id);
            break;
        case MessageToDSP_terminate_tag:
            comdrv_terminate();
            break;
        default:
            // XXX
            break;
    }

    return status == true ? 0 : -1;
}


/**
 * Initialize com module
 */
int com_init(void)
{
    return comdrv_init();
}


/**
 * Process communication between host and MPU, and return ASAP.
 */
int com_proc(void)
{
    int len;

    for (;;) {
        /*
         * Read message from UART.  If no message is available, return soon.
         */
        len = comdrv_read_protobuf(
                stream_buf, sizeof(stream_buf) / sizeof(pb_byte_t));

        if (len == -1)
            break;

        if (len < -1)
            comdrv_restart();

        /*
         * Decode message if available.
         */
        decode_msg(stream_buf, len);
    }

    return 0;
}


/**
 * Send a message to host
 *
 * @return -1 if failed to encode reply
 */
int com_send_msg(MessageToHost *reply)
{
    uint8_t c;

    pb_ostream_t stream =
        pb_ostream_from_buffer(stream_buf, sizeof(stream_buf));
    bool status;
    int message_length;

    status = pb_encode(&stream, MessageToHost_fields, reply);
    message_length = stream.bytes_written;

    if (status != true)
        return -1;

    comdrv_ensure_xmit_buffer_available(2 + message_length);

    /*
     * Send message length in 16-bit integer
     */
    c = (message_length >> 8) & 0xff;
    comdrv_write_block(&c, 1);
    c = message_length & 0xff;
    comdrv_write_block(&c, 1);

    /*
     * Finally send the reply message
     */
    comdrv_write_block(stream_buf, message_length);
    comdrv_flush();

    return 0;
}
