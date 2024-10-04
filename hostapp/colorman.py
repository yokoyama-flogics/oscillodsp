"""
Plotting Color Manager


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

DEFAULT_CH_COLORS = [
    "gold",
    "dodgerblue",
    "darkred",
    "darkblue",
]

DEFAULT_NEW_COLOR = "black"


class ColorManager:
    def __init__(self, confman, confname="chcolors"):
        self.confman = confman
        self.confname = confname

    def color(self, channel):
        """
        Return color of the channel
        """
        colors = self.__read_config()

        if channel >= len(colors):
            colors = self.__add_color(colors, channel)
            self.__store_config(colors)

        return colors[channel]

    def set_color(self, channel, color):
        """
        Set color of the channel
        """
        colors = self.__read_config()

        if channel >= len(colors):
            colors = self.__add_color(colors, channel)

        colors[channel] = color
        self.__store_config(colors)

    def all_colors(self):
        return self.__read_config()

    def set_all_colors(self, colors=[]):
        # If colors is [], just copy it to colors, but if None, copy defaults
        # to colors
        if colors is None:
            colors = DEFAULT_CH_COLORS
            save_required = False
        else:
            colors = colors
            save_required = True

        use_this_functionality = False
        if use_this_functionality:
            # Initialize all colors by defaults if number of 'colors' is fewer
            # than defaults.
            for ch in range(len(colors), len(DEFAULT_CH_COLORS)):
                colors.append(DEFAULT_CH_COLORS[ch])

        # if colors is not None:
        self.__store_config(colors, save_required=save_required)

    def __add_color(self, colors, channel):
        for ch in range(len(colors), channel + 1):
            colors.append(DEFAULT_NEW_COLOR)
        return colors

    def __read_config(self):
        colors = self.confman.get(self.confname)
        if colors is None:
            # In the case confman doesn't return colors, we need to reset.
            self.set_all_colors(None)
        return self.confman.get(self.confname)

    def __store_config(self, colors, save_required=True):
        self.confman.set(self.confname, colors, save_required)
