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

import asyncio
import logging
import math
import sys

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import Layout
from matplotlib.ticker import EngFormatter

from oscillodsp import dsp
from oscillodsp.oscillodsp_pb2 import TriggerMode, TriggerType
from oscillodsp.utils import Blinker, get_filename, modified_ylim

# Various definitions
DEFAULT_SAMPLE_QUANTIZE_BITS = 16
BLINK_LIST = ["Waiting", "Auto"]
DEFAULT_CH_COLOR = [
    "gold",
    "dodgerblue",
    "darkred",
    "darkblue",
    "black",
    "black",
    "black",
    "black",
]

# Define layouts
H_LAYOUT = Layout(width="150px")
V_LAYOUT = Layout(width="30px", height="4.1in")


def show_module_versions(modules):
    """
    Show Python and module versions
    """
    import importlib

    print("Python version:", sys.version)

    for m in modules:
        _ = importlib.import_module(m)
        print("{:s}: {:s}".format(m, _.__version__))


def observe(widget, trait_name):
    """
    This is required because may ipywidgets widgets don't accept decorator
    notation.

    Refer https://github.com/jupyter-widgets/ipywidgets/issues/717
    """

    def wrapper(func):
        widget.observe(func, trait_name)

    return wrapper


class Oscillo(widgets.HBox):
    """
    Main Oscillo class definition
    """

    def __init__(
        self,
        dsp_tty,
        dsp_bitrate,
        quantize_bits=DEFAULT_SAMPLE_QUANTIZE_BITS,
        loglevel=logging.WARNING,
        loghandler=logging.StreamHandler(sys.__stdout__),
        logformatter=logging.Formatter("oscillo.py: %(message)s"),
        dsp_loglevel=logging.WARNING,
    ):

        # Call widgets.HBox.__init__()
        # Refer https://kapernikov.com/ipywidgets-with-matplotlib/
        super().__init__()

        self.quantize_bits = quantize_bits

        # Set-up logger for debugging
        logger = logging.getLogger("oscillo")
        logger.setLevel(loglevel)
        loghandler.setFormatter(logformatter)
        logger.addHandler(loghandler)
        self.logger = logger

        # Identify underling OS (Linux, Windows, etc.) and determine asyncio
        # sleep length
        if sys.platform == "win32":
            self.sleep_len = 0.1
            self.logger.info(
                "Detected running on Windows, so using a special sleep length."
            )
        else:
            self.sleep_len = 0.01

        # Connecting to peer DSP
        self.peer = dsp.DSP(dsp_tty, dsp_bitrate, loglevel=dsp_loglevel)

        # Creating output object for Matplotlib figure
        output = widgets.Output()
        with output:
            self.fig, self.ax = plt.subplots(
                constrained_layout=True, figsize=(7, 4)
            )

        # Move the toolbar to the bottom
        self.fig.canvas.toolbar_position = "bottom"

        # Initialize other object variables which are related to plotting
        self.ch_active = 0  # channel currently paying attention by user
        self.trigmode = None
        self.trigtype = TriggerType.RisingEdge
        self.tscale = 0.0

        #
        # Define all widgets here
        #
        self.menu_ch = widgets.Dropdown(options=[], layout=H_LAYOUT)
        self.menu_trig = widgets.Dropdown(
            options=[
                ("Auto", TriggerMode.Auto),
                ("Normal", TriggerMode.Normal),
                ("Single", TriggerMode.Single),
            ],
            value=TriggerMode.Auto,
            layout=H_LAYOUT,
        )
        self.button_single = widgets.Button(description="Reset", disabled=True)
        self.text_trig_status = widgets.HTML("<b>Trigger Status</b>: Waiting")
        self.ftext_triglevel = widgets.FloatText(
            value=0.0, step=0.5, description="", layout=H_LAYOUT
        )
        self.button_stop = widgets.Button(
            description="Ready", button_style="primary"
        )
        self.button_save_image = widgets.Button(
            description="Save as Image File"
        )
        self.button_save_csv = widgets.Button(description="Save as CSV File")
        self.slider_mag = widgets.FloatSlider(
            value=1.0,
            min=0.1,
            max=1.91,
            step=0.1,
            orientation="vertical",
            layout=V_LAYOUT,
        )
        self.slider_ypos = widgets.FloatSlider(
            value=0.0,
            min=-1.0,
            max=1.0,
            orientation="vertical",
            layout=V_LAYOUT,
        )
        self.slider_tscale = widgets.FloatLogSlider(
            value=1 / 1e-3,  # reciprocal of time-scale
            base=10,
            min=0,
            max=9,
            step=1 / 3,
            orientation="horizontal",
            readout=False,
            layout=H_LAYOUT,
        )

        # Set Trigger Mode according to the menu selection
        self.trigmode_new = self.menu_trig.value  # for synchronous update
        self.triglevel_new = self.ftext_triglevel.value
        self.triglevel = 0.0

        #
        # Define callback functions respond GUI operations
        #
        @observe(self.menu_ch, "value")
        def _(change):
            self.ch_active = change.new
            self.slider_mag.value = self.mag[self.ch_active]
            self.slider_ypos.value = self.ypos[self.ch_active]

        @observe(self.menu_trig, "value")
        def _(change):
            self.trigmode_new = change.new

        @self.button_single.on_click
        def _(b):
            self.clear_trig = True

        @observe(self.ftext_triglevel, "value")
        def _(change):
            self.triglevel_new = change.new

        @self.button_stop.on_click
        def _(b):
            if self.stopped:
                for task in asyncio.all_tasks():
                    task.cancel()
                self.start()
            else:
                self.stopped = True
                self.button_stop.button_style = "danger"

        @self.button_save_image.on_click
        def _(b):
            s = get_filename(".png")
            plt.savefig(s)

        @self.button_save_csv.on_click
        def _(b):
            self.req_save_csv = True

        @observe(self.slider_mag, "value")
        def _(change):
            self.mag[self.ch_active] = change.new

        @observe(self.slider_ypos, "value")
        def _(change):
            self.ypos[self.ch_active] = change.new

        @observe(self.slider_tscale, "value")
        def _(change):
            self.tscale_new = 1 / change.new

        # Once call DSP to obtain various information need to set-up variables
        config_reply = self.peer.config(
            resolution=self.quantize_bits,
            trigmode=self.trigmode_new,
            trigtype=self.trigtype,
            ch_trig=0,
            triglevel=self.triglevel,
            timescale=0.0,
        )  # timescale as '0.0' means "Don't update timescale"

        # Set-up mag and ypos
        self.mag = []
        self.ypos = []
        for ch in config_reply.chconfig:
            self.mag.append(1.0)
            center = (ch.min + ch.max) / 2
            width = ch.max - ch.min
            self.ypos.append(-2.0 * center / width)

        # Create sub_ax (multiple ax on one subplot) of required numbers
        self.sub_ax = []
        for i in range(len(config_reply.chconfig) - 1):
            self.sub_ax.append(self.ax.twinx())

        # Configure Channel menu
        self.options = []
        self.view_enabled_ch = []
        for idx, ch in enumerate(config_reply.chconfig):
            self.options.append(("{:d}: {:s}".format(idx, ch.name), idx))
            self.view_enabled_ch.append(True)
        self.menu_ch.options = self.options

        # Configure default time-scale
        self.tscale_new = config_reply.default_timescale
        self.slider_tscale.min = math.log10(1 / config_reply.max_timescale)

        # Finally assemble all widgets in one box
        self.controls = widgets.HBox(
            [
                widgets.VBox(
                    [
                        widgets.VBox(
                            [
                                widgets.Box(layout=Layout(height="10px")),
                                widgets.HTML("Scale&nbsp;&nbsp;Pos"),
                            ],
                            layout=Layout(height="40px"),
                        ),
                        widgets.HBox(
                            [
                                self.slider_mag,
                                self.slider_ypos,
                            ]
                        ),
                    ]
                ),
                widgets.VBox(
                    [
                        widgets.HTML("<b>Active Channel</b>"),
                        self.menu_ch,
                        widgets.HTML("<b>Trigger Mode</b>"),
                        self.menu_trig,
                        self.button_single,
                        self.text_trig_status,
                        widgets.HTML("<b>Trigger Level</b>"),
                        self.ftext_triglevel,
                        widgets.HTML("<b>Horizontal Scale</b>"),
                        self.slider_tscale,
                        widgets.HTML("<hr>"),
                        self.button_stop,
                        self.button_save_image,
                        self.button_save_csv,
                    ]
                ),
            ]
        )
        self.children = [output, self.controls]

    # To allow GUI operations while repeating plot updates, we need to run
    # this function in background.  After experienced Python threading
    # functions didn't work correctly, finally adopted asyncio.
    #
    # Refer https://github.com/voila-dashboards/voila/issues/431
    async def oscillo_start(self):
        self.stopped = False
        self.clear_trig = False
        self.req_save_csv = False
        self.button_stop.description = "Run/Stop"
        self.button_stop.button_style = "success"

        blinker = Blinker()
        old_status = ""
        triggered = False
        last_ylim = None
        formatter = EngFormatter()

        while True:
            # When requested by UI, clear triggered flag synchronously
            if self.clear_trig:
                triggered = False
                self.clear_trig = False  # Reset the request

            # When requested by UI, clear triggered flag synchronously
            if (
                self.trigmode_new != self.trigmode
                or self.tscale_new != self.tscale
                or self.triglevel_new != self.triglevel
            ):
                self.trigmode = self.trigmode_new
                self.tscale = self.tscale_new
                self.triglevel = self.triglevel_new
                triggered = False
                self.button_single.disabled = (
                    self.trigmode != TriggerMode.Single
                )
                config_reply = self.peer.config(
                    resolution=self.quantize_bits,
                    trigmode=self.trigmode,
                    trigtype=self.trigtype,
                    ch_trig=0,
                    triglevel=self.triglevel,
                    timescale=self.tscale,
                )
                self.last_reply = config_reply

            # Once triggered for single-shot mode, re-use wave data
            if self.trigmode != TriggerMode.Single or not triggered:
                waves = self.peer.get_waves()  # Trying update wave data
                if len(waves.wave) > 0:
                    triggered = waves.triggered

            # Determine if plotting is required
            need_plot = len(waves.wave) > 0
            blank_screen = False

            # Update trigger status message
            if self.trigmode == TriggerMode.Auto:
                if triggered:
                    new_status = "Triggered"
                else:
                    new_status = "Auto"
            elif self.trigmode == TriggerMode.Normal:
                if need_plot:
                    new_status = "Triggered"
                else:
                    new_status = "Waiting"
            else:
                if triggered:
                    new_status = "Stopped"
                else:
                    new_status = "Waiting"
                    blank_screen = True

            # Blinking trigger status message
            if new_status != old_status:
                blinker.reset()
            if new_status in BLINK_LIST and not blinker.active():
                msg_status = ""
            else:
                msg_status = new_status
            self.text_trig_status.value = (
                "<b>Trigger Status</b>: " + msg_status
            )
            old_status = new_status

            if need_plot:
                # Generate CSV file header if required
                csv_samples = []
                if self.req_save_csv:
                    csv_printer = open(get_filename(".csv"), "w")
                    csv_printer.write("time [sec]")
                    for ch in self.last_reply.chconfig:
                        csv_printer.write(
                            ",{:s} [{:s}]".format(ch.name, ch.unit)
                        )
                    csv_printer.write("\n")

                # Now we can determine samples in a wave
                n_xsamples = len(waves.wave[0].samples)
                xlim = (-self.tscale / 2, self.tscale / 2)

                # ax.set_facecolor('#404040')
                # ax.axhline(y=0, color='k')
                # ax.axvline(x=0, color='k')

                chconfig_active = self.last_reply.chconfig[self.ch_active]

                if blank_screen:
                    self.ax.clear()
                    for ax in self.sub_ax:
                        ax.clear()
                        ax.set_axis_off()

                    self.ax.set_xlim(xlim)

                    if last_ylim is not None:
                        self.ax.set_ylim(last_ylim)
                else:
                    lines = []
                    # xser is common among multiple channels, so assign here
                    xser = np.linspace(xlim[0], xlim[1], n_xsamples)

                    ct_sub_ax = 0
                    for idx, wave in enumerate(waves.wave):
                        chconfig_idx = self.last_reply.chconfig[idx]

                        if idx == self.ch_active:
                            cur_ax = self.ax
                        else:
                            cur_ax = self.sub_ax[ct_sub_ax]
                            ct_sub_ax += 1

                        cur_ax.clear()

                        # Show only active channel axis
                        if idx != self.ch_active:
                            cur_ax.set_axis_off()

                        # Convert wave samples to original float values
                        ylim = (chconfig_idx.min, chconfig_idx.max)
                        yser = np.asarray(wave.samples, dtype=np.float32)
                        yser /= (1 << self.quantize_bits) / (ylim[1] - ylim[0])
                        yser += (ylim[0] + ylim[1]) / 2

                        # Keep yser samples for CSV output
                        if self.req_save_csv:
                            csv_samples.append(yser)

                        # Use a special ylim which taking account of mag and
                        # ypos, and set_ylim()
                        last_ylim = modified_ylim(
                            ylim, self.mag[idx], self.ypos[idx]
                        )  # save for blank_screen
                        cur_ax.set_ylim(last_ylim)

                        # Generating label for line plot
                        label = chconfig_idx.name
                        if idx == self.ch_active:
                            label += " (active)"

                        # Finally plot line of a channel
                        if self.view_enabled_ch[idx]:
                            (l,) = cur_ax.plot(
                                xser, yser, DEFAULT_CH_COLOR[idx], label=label
                            )

                            # Append the line to lines[] to show legend on the
                            # screen.
                            # Note that this is required ONLY for legend
                            # purpose.  Even without this "lines", plottings
                            # themselves are accomplished.
                            lines.append(l)

                # xlim is common among channels, so process here
                self.ax.set_xlim(xlim)
                self.ax.xaxis.set_major_formatter(formatter)
                self.ax.set_xlabel("[sec]")

                # ylim is configured for currently active channel
                self.ax.yaxis.set_major_formatter(formatter)
                self.ax.set_ylabel(
                    "{:s} [{:s}]".format(
                        chconfig_active.name, chconfig_active.unit
                    )
                )

                # Show legend here
                if len(lines) > 0:
                    self.ax.legend(
                        lines,
                        [_.get_label() for _ in lines],
                        loc="upper left",
                        # labelcolor='white',
                        facecolor="lightgray",
                        # edgecolor='white'
                    )

                # Show grid and finally draw everything
                self.ax.grid(True)
                self.fig.canvas.draw()

                # Save to CSV file if required
                if self.req_save_csv:
                    for i in range(n_xsamples):
                        csv_printer.write("{:e}".format(xser[i]))
                        for ch_id in range(len(self.last_reply.chconfig)):
                            csv_printer.write(
                                ",{:e}".format(csv_samples[ch_id][i])
                            )
                        csv_printer.write("\n")
                    csv_printer.close()
                    self.req_save_csv = False

            if self.stopped:
                break

            await asyncio.sleep(self.sleep_len)

    def start(self):
        """
        Start oscilloscope
        """
        asyncio.create_task(self.oscillo_start())

    def close(self):
        """
        Close oscilloscope
        """
        for task in asyncio.all_tasks():
            task.cancel()
        plt.close("all")
        self.peer.terminate()
        del self.peer
