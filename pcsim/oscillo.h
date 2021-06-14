#ifndef __OSCILLO_H__

#include "config.h"
#include "oscillodsp.pb.h"

typedef struct {
    bool enabled;
} dsp_channel_config_t;

int oscillo_init(float sample_rate, float default_timescale);
int oscillo_reinit(void);
int oscillo_pass_one(int ch, sample_t val);
int oscillo_config(Configure arg_config, ConfigReply *arg_config_reply);
int oscillo_config_ch(const char *name, const char *unit, float min, float max);
int oscillo_get_waves(WaveGroup *waves);
float oscillo_get_demo1_value(bool enabled);
float oscillo_get_demo2_value(bool enabled);
float oscillo_get_demo3_value(bool enabled);

#define __OSCILLO_H__
#endif /* ! defined(__OSCILLO_H__) */
