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
 * OscilloDSP: Virtual Oscilloscope Library
 *
 * Written by Atsushi Yokoyama, Firmlogics (contact@flogics.com)
 */


#undef DEBUG

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>
#include <math.h>
#include "config.h"
#include "common.h"
#include "oscillo.h"
#include "com.h"
#include "oscillodsp.pb.h"

#ifndef M_PI
#define M_PI    3.14159265358979323846264338327950288
#endif /* !defined(M_PI) */

enum {
    N_CHANNELS = pb_arraysize(WaveGroup, wave),
    N_WAVE_SAMPLES = pb_arraysize(Wave, samples),
};

static buffer_t buffer[N_CHANNELS][LEN_BUFFER];
static ConfigReply config_reply;
static dsp_channel_config_t dsp_ch_config[N_CHANNELS];
static int idx_write_buffer[N_CHANNELS];
static Configure config;


/**
 * Correct buffer index
 *
 * Refer https://www.lemoda.net/c/modulo-operator/
 */
#define MOD(a, b) ((((a) % (b)) + (b)) % (b))
static int correct_idx(int idx)
{
    return MOD(idx, LEN_BUFFER);
}


/**
 * Convert float value to buffer_t value
 *
 * @param ch corresponding channel ID
 * @param val is original float value
 */
static buffer_t f_to_bufval(int ch, float val, int *err)
{
    long tmp_val;
    long drange;
    long max_val;
    long min_val;
    float mul;
    float offset;
    ChannelConfig *cc;

    if (ch < 0 || ch >= N_CHANNELS) {
        *err = -1;
        return 0;
    }

    if (! dsp_ch_config[ch].enabled) {
        *err = -2;
        return 0;
    }

    cc = &config_reply.chconfig[ch];

    /*
     * Prepare constant values to convert val to integer which fits buffer_t.
     */
    drange = 1 << (config.resolution - 1);

    // corresponds to 0x7f...ff (in two's complement)
    max_val = drange - 1;
    // corresponds to 0x80...00 (ditto)
    min_val = - drange;
    // coefficient multiplying to the original value
    mul = 2.0f * drange / (cc->max - cc->min);
    // center of the signal range
    offset = (cc->max + cc->min) / 2.0f;

    /*
     * Convert val and check if the converted value doesn't overflow.
     */
    tmp_val = (long) ((val - offset) * mul);
    if (tmp_val > max_val)
        tmp_val = max_val;
    else if (tmp_val < min_val)
        tmp_val = min_val;

    *err = 0;
    return (buffer_t) tmp_val;
}


/**
 * Initialize oscillo library
 *
 * @param sample_rate is sampling rate [Hz]
 * @param default_timescale is length of frame width time [seconds]
 */
int oscillo_init(float sample_rate, float default_timescale)
{
    memset(buffer, 0, sizeof(buffer));
    memset(&config_reply, 0, sizeof(config_reply));
    memset(dsp_ch_config, 0, sizeof(dsp_ch_config));
    memset(idx_write_buffer, 0, sizeof(idx_write_buffer));

    config.resolution = 8;  // set because resolution '0' is not good default
    config.trigmode = TriggerMode_Auto;
    config.trigtype = TriggerType_RisingEdge;
    config.ch_trig = 0;
    config.triglevel = 0.0f;

    config_reply.samplerate = sample_rate;
    config_reply.default_timescale = default_timescale;
    config_reply.max_timescale = (float) LEN_BUFFER / sample_rate;

    return 0;
}


/**
 * Re-initialize oscillo library
 */
int oscillo_reinit(void)
{
    return oscillo_init(
            config_reply.samplerate, config_reply.default_timescale);
}


/**
 * Pass a sample value to oscillo library
 *
 * @param ch is channel ID starting at 0
 * @param val is passed sample value.  val _should_ be between -1 to 1.
 */
int oscillo_pass_one(int ch, sample_t val)
{
    int err;

    if (ch < 0 || ch >= N_CHANNELS)
        return -1;

    if (! dsp_ch_config[ch].enabled)
        return -2;

    buffer[ch][idx_write_buffer[ch]] = f_to_bufval(ch, val, &err);
    if (err)
        return err;

    /*
     * Update idx_write_buffer
     */
    idx_write_buffer[ch] = correct_idx(idx_write_buffer[ch] + 1);

    return 0;
}


/**
 * Process oscillo library
 *
 * @param val is passed sample value
 */
int oscillo_proc(void)
{
    return 0;
}


/**
 * Configure oscillo mode
 */
int oscillo_config(Configure arg_config, ConfigReply *arg_config_reply)
{
    if (arg_config.resolution > sizeof(buffer_t) * 8)
        return -1;

    if (arg_config.trigmode < TriggerMode_Auto)
        return -1;

    if (arg_config.trigmode > TriggerMode_Single)
        return -1;

    if (arg_config.trigtype < TriggerType_RisingEdge)
        return -1;

    if (arg_config.trigtype > TriggerType_FallingEdge)
        return -1;

    if (arg_config.ch_trig >= N_CHANNELS)
        return -1;

    if (! dsp_ch_config[arg_config.ch_trig].enabled)
        return -2;

    memcpy(&config, &arg_config, sizeof(Configure));

    /*
     * If specified timescale is 0.0f as a special value, we recover default
     * timescale.
     */
    if (arg_config.timescale == 0.0f)
        config.timescale = config_reply.default_timescale;

    memcpy(arg_config_reply, &config_reply, sizeof(ConfigReply));

    return 0;
}


/**
 * Configure oscillo channel
 *
 * @param name is channel name
 * @param unit is unit (V, A, sec, etc.)
 * @param min is expected minimum value of any samples
 * @param max is expected maximum value of any samples
 *
 * @return channel ID starting at 0
 */
int oscillo_config_ch(const char *name, const char *unit, float min, float max)
{
    int ch;
    ChannelConfig *cc;

    if (config_reply.chconfig_count >= N_CHANNELS)
        return -1;

    ch = config_reply.chconfig_count;
    cc = &config_reply.chconfig[ch];

    strncpy(cc->name, name, pb_arraysize(ChannelConfig, name) - 1);
    cc->name[pb_arraysize(ChannelConfig, name) - 1] = '\0';

    strncpy(cc->unit, unit, pb_arraysize(ChannelConfig, unit) - 1);
    cc->unit[pb_arraysize(ChannelConfig, unit) - 1] = '\0';

    cc->min = min;
    cc->max = max;

    dsp_ch_config[ch].enabled = true;

    config_reply.chconfig_count ++;

    return ch;
}


/**
 * Scale an index in wave samples, to index in buffer[][] according to
 * timescale and sampling rate
 *
 * @param idx is index in wave samples
 */
static int scale_index(int idx)
{
    float t = (float) idx / N_WAVE_SAMPLES * config.timescale;

    return (int) (t * config_reply.samplerate);
}


/**
 * Compare for triggering edge detection
 *
 * For rising edge, return true if v1 > v2.
 * Return false in the falling edge case.
 *
 * @param v1, v2
 */
static bool comp_trig_edge(buffer_t v1, buffer_t v2)
{
    if (config.trigtype == TriggerType_RisingEdge)
        return v1 > v2;
    else
        return v1 < v2;
}


/**
 * Determine tail sample position to send
 *
 * @return index in buffer
 */
static int get_pos(bool *triggered)
{
    int i;
    int ch;
    int err;
    int pos_buf;
    int tail_pos;
    int int_triglevel;
    int margin_x;
    int margin_y;
    buffer_t cur_val;
    buffer_t past_val;
    bool found;
    bool cond_met;

    ch = config.ch_trig;
    int_triglevel = f_to_bufval(ch, config.triglevel, &err);
    if (err)
        return err;

    found = false;

    cond_met = false;
    tail_pos = correct_idx(idx_write_buffer[ch] - 1);
    margin_x = (int) ((float) HIST_MARGIN_X * N_WAVE_SAMPLES);
    margin_y = (int) ((float) HIST_MARGIN_Y * (1 << config.resolution));

    for (i = 0; i < N_WAVE_SAMPLES; i ++) {
        pos_buf = correct_idx(tail_pos - scale_index(i + N_WAVE_SAMPLES / 2));

        assert(pos_buf >= 0);
        assert(pos_buf < LEN_BUFFER);

        cur_val = buffer[ch][pos_buf];
        if (comp_trig_edge(cur_val, int_triglevel))
            cond_met = true;

        past_val = buffer[ch][correct_idx(pos_buf - margin_x)];
        if (cond_met &&
                comp_trig_edge(cur_val - margin_y, past_val) &&
                comp_trig_edge(int_triglevel, cur_val)) {
            found = true;
            pos_buf = correct_idx(pos_buf + scale_index(N_WAVE_SAMPLES / 2));
            break;
        }
    }

    *triggered = found;

    if (! found) {
        if (config.trigmode == TriggerMode_Normal)
            pos_buf = -1;
        else
            pos_buf = correct_idx(idx_write_buffer[ch] - 1);
    }

    return pos_buf;
}


/**
 * Return a wave frame
 */
static int get_wave(int ch, int pos_buf, Wave *wave)
{
    int i;
    int idx;

    if (ch < 0 || ch >= N_CHANNELS)
        return -1;

    if (! dsp_ch_config[ch].enabled)
        return -2;

    wave->ch_id = ch;

    assert(pos_buf >= 0);
    assert(pos_buf <= LEN_BUFFER);

    for (i = 0; i < N_WAVE_SAMPLES; i ++) {
        idx = correct_idx(pos_buf - scale_index(i));

        assert(idx >= 0);
        assert(idx < LEN_BUFFER);

        /*
         * Copy samples in buffer[ch][] to wave.samples[]
         */
        wave->samples[N_WAVE_SAMPLES - 1 - i] = buffer[ch][idx];
    }

    return 0;
}


/**
 * Return group of wave frames
 */
int oscillo_get_waves(WaveGroup *waves)
{
    int ch;
    int pos_buf;
    bool triggered;

    pos_buf = get_pos(&triggered);

    if (pos_buf < 0) {  // Implies TriggerMode_Normal
        waves->triggered = false;
        waves->wave_count = 0;
        return 0;
    }

    /*
     * Only when triggered, send wave frames
     */
    for (ch = 0; ch < config_reply.chconfig_count; ch ++)
        get_wave(ch, pos_buf, &waves->wave[ch]);

    waves->triggered = triggered;
    waves->wave_count = config_reply.chconfig_count;

    return 0;
}


/*
 * Return a float random value
 *
 * @param amp is amplitude of the random value
 */
static float get_noise(float amp)
{
    return amp * (float) rand() / RAND_MAX - amp / 2;
}


/**
 * Return a demo (version 1) value
 */
float oscillo_get_demo1_value(bool enabled)
{
    static int deg = 0;
    float val;
    float noise;

    noise = get_noise(0.12);
    val = 0.5 + noise;
    if (enabled) {
        val += 3.0 * sinf((float) deg / 180 * M_PI);
        val += 0.3 * sinf((float) deg * 8 / 180 * M_PI);
    }

    deg ++;
    if (deg >= 360)
        deg = 0;

    return val;
}


/**
 * Return a demo (version 2) value
 */
float oscillo_get_demo2_value(bool enabled)
{
    static int deg = 0;
    float val;
    float noise;

    noise = get_noise(0.12);
    val = noise;
    if (enabled)
        val += 1.5 * (deg % 180 < 90 ? 1.0 : -1.0);

    deg ++;
    if (deg >= 360)
        deg = 0;

    return val;
}
