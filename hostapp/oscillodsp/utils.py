"""
Copyright (c) 2020-2021, Chubu University and Firmlogics

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
"""

from datetime import datetime


def get_filename(ext=".out"):
    """
    Return a file name which contains date-time string.
    """
    return datetime.now().strftime("%Y%m%d-%H%M%S") + ext


def modified_ylim(ylim, mag, ypos):
    """
    Return a special ylim (tuple) taking account mag and ypos.

    You're not required to understand this formula.  Just obtained a linear
    function which conforms to the relation between 'y' and 'x'.
    """
    width = (ylim[1] - ylim[0]) / mag
    new_ylim_0 = -(width / 2) * (ypos + 1)
    return (new_ylim_0, new_ylim_0 + width)


def run_pcsim(pcsim_path):
    import atexit
    import os
    import time

    PTY_NAME = "ptyname.txt"
    TIME_MARGIN = 1.0

    fpath, fname = os.path.split(pcsim_path)

    def kill_sim():
        os.system("killall {:s}".format(fname))

    os.system("cd {:s} && make".format(fpath))
    if not os.path.isfile(pcsim_path):
        raise (Exception("PC simulator can't be compiled"))

    os.system("{:s} &".format(pcsim_path))  # Run in background

    # When Jupyter kernel shutdowns, ensure all pcsim(s) are terminated
    atexit.register(kill_sim)

    # Wait to ensure ptyname.txt is created
    while not os.path.exists(PTY_NAME):
        time.sleep(0.01)

    while time.time() - os.stat(PTY_NAME).st_mtime > TIME_MARGIN:
        time.sleep(0.01)

    return open("ptyname.txt").read()


class Blinker:
    """
    A kind of periodic timer function

    Method active() returns True in the first half of the period, and return
    False otherwise.
    """

    def __init__(self, period=1.0):
        self.period = period
        self.reset()

    def active(self):
        passed = datetime.now() - self.start
        sec_passed = passed.seconds + passed.microseconds / 1e6
        sec_passed %= self.period
        return sec_passed < self.period / 2

    def reset(self):
        self.start = datetime.now()
