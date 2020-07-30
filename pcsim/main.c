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


#include <sys/time.h>
#include "com.h"
#include "oscillo.h"

int main(int argc, char **argv)
{
    bool active;
    struct timeval tv;
    int ch0;
    int ch1;

    com_init();
    oscillo_init(1e6, 1e-3);

    ch0 = oscillo_config_ch("input", "volts", -4.0, 5.0);
    ch1 = oscillo_config_ch("output", "amperes", -3.0, 3.0);

    for (;;) {
        com_proc();

        gettimeofday(&tv, NULL);

        active = tv.tv_sec % 4 < 2;
        oscillo_pass_one(ch0, oscillo_get_demo1_value(active));
        oscillo_pass_one(ch1, oscillo_get_demo2_value(true));
    }

    return 0;
}
