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

import logging
import struct
import sys
from datetime import datetime, timedelta

from . import oscillodsp_pb2

FTDI_PRODUCT_IDS = {0xA6D0}
DEFAULT_TIMEOUT_SECONDS = 3.0  # wait forever if None


def dump(s):
    """
    Debugging functionality to check received raw bytes.
    Currently not used.
    @param s is buffer
    """
    for i in range(len(s)):
        if i % 16 == 0:
            sys.stdout.write("{:04x}: ".format(i))
        sys.stdout.write("{:02x} ".format(s[i]))
        if i % 16 == 15:
            print("")
    print("")


def open_interface(tty, bitrate, logger=None):
    if logger:
        logger.debug("open_interface: {} {:d}".format(tty, bitrate))

    # Different procedures are required for PyFTDI and PySerial
    if len(tty) > 4 and tty[:4] == "ftdi":
        import pyftdi.serialext
        from pyftdi.ftdi import Ftdi

        for pid in FTDI_PRODUCT_IDS:
            try:
                Ftdi.add_custom_product(Ftdi.DEFAULT_VENDOR, pid)
            except ValueError:
                pass

        if logger:
            logger.info("Using pyftdi")

        Ftdi.show_devices()
        ser = pyftdi.serialext.serial_for_url(
            tty, baudrate=bitrate, timeout=DEFAULT_TIMEOUT_SECONDS
        )
        # XXX should raise exception for illegal caudrate
    else:
        import serial

        if logger:
            logger.debug("Using pyserial")
        try:
            ser = serial.Serial(tty, bitrate, timeout=DEFAULT_TIMEOUT_SECONDS)
        except serial.SerialException:
            raise

    return ser


class DSP:
    """
    DSP class definition to abstract communication with peer DSP
    """

    def __init__(
        self,
        tty,
        bitrate,
        loglevel=logging.WARNING,
        loghandler=logging.StreamHandler(sys.__stdout__),
        console_handler=None,
        file_handler=None,
        logformatter=logging.Formatter("dsp.py: %(message)s"),
    ):

        self.debug_ct = 0

        logger = logging.getLogger("dsp")
        logger.setLevel(loglevel)

        if console_handler:
            console_handler.setFormatter(logformatter)
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
        else:
            # For backward compatibility
            loghandler.setFormatter(logformatter)
            logger.addHandler(loghandler)
        self.logger = logger

        self.ser = open_interface(tty, bitrate, self.logger)

        self.msg = oscillodsp_pb2.MessageToDSP()
        self.id = 0
        self.last_recvdtime = datetime.now()
        self.recvd_bytes = 0

    def get_logger(self):
        return self.logger

    def __del__(self):
        self.logger.info("Deleting DSP object")
        del self.logger

    def send_msg(self, withId=True):
        """
        Send a message to DSP
        @param withId is if we need to add sequential ID for consistency check
        """
        if withId:
            self.msg.id = self.id
        else:
            self.msg.id = 0

        s = self.msg.SerializeToString()
        length = len(s)

        self.logger.debug("send_msg length = {:d}".format(length))

        self.ser.write(struct.pack("!H", length))
        self.ser.write(s)
        self.ser.flush()

        if withId:
            last_sent_id = self.id
            self.id += 1
            return last_sent_id
        else:
            return None

    def recv_msg_raw(self):
        """
        Receive a raw message from DSP
        """
        s = self.ser.read(2)
        if len(s) < 2:
            raise Exception("Timeout.  No response from DSP.")

        length = struct.unpack("!H", s)[0]
        self.logger.debug("recv_msg_raw length = {:d}".format(length))

        self.recvd_bytes += 2 + length
        time_delta = datetime.now() - self.last_recvdtime
        if time_delta > timedelta(seconds=1):
            sec = time_delta.seconds + time_delta.microseconds / 1e6
            self.logger.info(
                "recv rate = {:5.1f} kbps".format(  # yapf: disable
                    self.recvd_bytes * 8 / sec / 1e3
                )
            )
            self.recvd_bytes = 0
            self.last_recvdtime = datetime.now()

        reply = oscillodsp_pb2.MessageToHost()
        reply.ParseFromString(self.ser.read(length))

        return reply

    def recv_msg(self, id_when_sent=None):
        """
        Receive a message from DSP and also check any errors
        @param id_when_sent is expected ID which will come from DSP peer
        """
        reply = self.recv_msg_raw()

        if id_when_sent is not None and reply.id != id_when_sent:
            self.logger.error("[ERROR] ID mismatch:")
            self.logger.error(
                "  expected={:d} received={:d}".format(  # yapf: disable
                    id_when_sent, reply.id
                )
            )

        # XXX  Don't we have much better way?
        if reply.HasField("ack") and reply.ack.err != oscillodsp_pb2.NoError:
            raise Exception(
                "reply.ack has error: {:s}".format(
                    oscillodsp_pb2._ERRORCODE.values[reply.ack.err].name
                )
            )

        return reply

    def echo_request(self, content):
        """
        Message to DSP: EchoRequest
        @param content is echo message to DSP peer
        """
        self.msg.echoreq.content = content
        id = self.send_msg()
        return self.recv_msg(id).echorep.content

    def config(
        self,
        resolution,
        trigmode,
        trigtype,
        ch_trig=0,
        triglevel=0,
        timescale=0.0,
    ):
        """
        Message to DSP: Configure
        @param resolution is number of quantization bits of each signal sample.
               16 or 8 are suitable but smaller values help to reduce data
               traffic from DSP to host
        @param trigmode is triggering mode (auto, normal, single, etc.)
        @param trigtype is triggering type (rising/falling edges)
        @param ch_trig is channel ID which is used as trigger
        @param triglevel is triggering level (physical value in volts, etc.)
        @param timescale is time length (in seconds) corresponds to
               oscilloscope screen width
        """
        DEBUG_TIMEOUT = False
        if DEBUG_TIMEOUT:
            self.debug_ct += 1
            print("debug_ct:", self.debug_ct)
            if self.debug_ct > 3:
                raise Exception("Timeout.  No response from DSP.")

        self.msg.config.resolution = resolution
        self.msg.config.trigmode = trigmode
        self.msg.config.trigtype = trigtype
        self.msg.config.ch_trig = ch_trig
        self.msg.config.triglevel = triglevel
        self.msg.config.timescale = timescale
        id = self.send_msg()
        reply = self.recv_msg(id).configreply
        if reply.err != oscillodsp_pb2.NoError:
            raise Exception("Configuration Error")
        return reply

    def get_waves(self):
        """
        Message to DSP: GetWaveGroup
        Returns a WaveGroup object
        """
        DEBUG_TIMEOUT = False
        if DEBUG_TIMEOUT:
            self.debug_ct += 1
            print("debug_ct:", self.debug_ct)
            if self.debug_ct > 10:
                raise Exception("Timeout.  No response from DSP.")

        self.msg.getwave.SetInParent()
        id = self.send_msg()
        return self.recv_msg(id).wavegroup

    def terminate(self):
        """
        Message to DSP: Terminate
        """
        self.logger.info("Terminating peer DSP")
        self.msg.terminate.SetInParent()
        self.send_msg()

    def discard(self):
        """
        Discard any bytes in transmit or receive buffers
        """
        while self.ser.in_waiting > 0 or self.ser.out_waiting > 0:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

    def check(self):
        """
        Check and show transmit and receive buffer status
        """
        self.logger.warning("In check()")
        self.logger.warning(
            "  in: {:d} out: {:d}\n".format(  # yapf: disable
                self.ser.in_waiting, self.ser.out_waiting
            )
        )
